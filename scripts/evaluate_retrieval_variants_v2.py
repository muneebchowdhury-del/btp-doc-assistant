import csv
import math
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass


# Allow imports from project root.
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from app import (
    get_embedding_model,
    get_hana_connection,
    vector_to_string
)


MODEL_NAME = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL_NAME = os.getenv(
    "V2_RERANKER_MODEL_NAME",
    "Xenova/ms-marco-MiniLM-L-6-v2"
)

CALIBRATION_FILE = "data/retrieval_calibration_v2.csv"
TABLE_NAME = "DOCUMENT_CHUNKS_V2"

DENSE_CANDIDATE_CHUNKS = int(
    os.getenv(
        "V2_DENSE_CANDIDATE_CHUNKS",
        "50"
    )
)
LEXICAL_CANDIDATE_CHUNKS = int(
    os.getenv(
        "V2_LEXICAL_CANDIDATE_CHUNKS",
        "50"
    )
)
RRF_K = int(
    os.getenv(
        "V2_RRF_K",
        "60"
    )
)
RERANK_BATCH_SIZE = int(
    os.getenv(
        "V2_RERANK_BATCH_SIZE",
        "32"
    )
)


TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+"
)


@dataclass
class Chunk:
    chunk_id: int
    document_id: str
    chunk_index: int
    title: str
    topic: str
    source_url: str
    chunk_text: str
    dense_score: float | None = None
    lexical_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: float | None = None


@dataclass
class Variant:
    key: str
    label: str


VARIANTS = [
    Variant(
        "A",
        "Dense baseline"
    ),
    Variant(
        "B",
        "Hybrid RRF"
    ),
    Variant(
        "C",
        "Dense + cross-encoder reranking"
    ),
    Variant(
        "D",
        "Hybrid RRF + cross-encoder reranking"
    )
]


def load_queries():
    with open(
        CALIBRATION_FILE,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(
                file
            )
        )


def is_supported(item):
    return item["EXPECTED_SUPPORTED"].strip() == "1"


def tokenize(text):
    return [
        token.lower()
        for token in TOKEN_PATTERN.findall(
            text or ""
        )
    ]


def fetch_dense_chunks(question):
    model = get_embedding_model()

    embedding_start = time.perf_counter()
    query_vector = list(
        model.query_embed(
            [question]
        )
    )[0]
    embedding_ms = (
        time.perf_counter() - embedding_start
    ) * 1000

    connection = get_hana_connection()
    cursor = connection.cursor()

    try:
        hana_start = time.perf_counter()

        cursor.execute(
            f"""
            SELECT
                "CHUNK_ID",
                "DOCUMENT_ID",
                "CHUNK_INDEX",
                "TITLE",
                "TOPIC",
                "SOURCE_URL",
                "CHUNK_TEXT",
                COSINE_SIMILARITY(
                    "EMBEDDING",
                    TO_REAL_VECTOR(?)
                ) AS "SCORE"
            FROM "{TABLE_NAME}"
            WHERE "EMBEDDING" IS NOT NULL
            ORDER BY "SCORE" DESC
            """,
            (
                vector_to_string(
                    query_vector
                ),
            )
        )

        rows = cursor.fetchall()
        hana_ms = (
            time.perf_counter() - hana_start
        ) * 1000

    finally:
        cursor.close()
        connection.close()

    chunks = []

    for row in rows:
        chunks.append(
            Chunk(
                chunk_id=int(row[0]),
                document_id=row[1],
                chunk_index=int(row[2]),
                title=row[3] or "",
                topic=row[4] or "",
                source_url=row[5] or "",
                chunk_text=row[6] or "",
                dense_score=float(row[7])
            )
        )

    return (
        chunks,
        embedding_ms,
        hana_ms
    )


def fetch_corpus_chunks():
    connection = get_hana_connection()
    cursor = connection.cursor()

    try:
        hana_start = time.perf_counter()

        cursor.execute(
            f"""
            SELECT
                "CHUNK_ID",
                "DOCUMENT_ID",
                "CHUNK_INDEX",
                "TITLE",
                "TOPIC",
                "SOURCE_URL",
                "CHUNK_TEXT"
            FROM "{TABLE_NAME}"
            WHERE "CHUNK_TEXT" IS NOT NULL
            ORDER BY "CHUNK_ID"
            """
        )

        rows = cursor.fetchall()
        hana_ms = (
            time.perf_counter() - hana_start
        ) * 1000

    finally:
        cursor.close()
        connection.close()

    chunks = []

    for row in rows:
        chunks.append(
            Chunk(
                chunk_id=int(row[0]),
                document_id=row[1],
                chunk_index=int(row[2]),
                title=row[3] or "",
                topic=row[4] or "",
                source_url=row[5] or "",
                chunk_text=row[6] or ""
            )
        )

    return (
        chunks,
        hana_ms
    )


def clone_chunk(chunk):
    return Chunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        title=chunk.title,
        topic=chunk.topic,
        source_url=chunk.source_url,
        chunk_text=chunk.chunk_text,
        dense_score=chunk.dense_score,
        lexical_score=chunk.lexical_score,
        fused_score=chunk.fused_score,
        rerank_score=chunk.rerank_score
    )


def build_bm25_index(chunks):
    tokenized_documents = {}
    document_frequency = Counter()
    total_length = 0

    for chunk in chunks:
        text = " ".join(
            [
                chunk.title,
                chunk.topic,
                chunk.chunk_text
            ]
        )
        tokens = tokenize(
            text
        )
        tokenized_documents[chunk.chunk_id] = tokens
        total_length += len(tokens)

        for token in set(tokens):
            document_frequency[token] += 1

    average_length = (
        total_length / len(chunks)
        if chunks
        else 0.0
    )

    return {
        "tokens": tokenized_documents,
        "document_frequency": document_frequency,
        "average_length": average_length,
        "document_count": len(chunks)
    }


def bm25_rank(question, chunks, bm25_index):
    query_terms = tokenize(
        question
    )

    query_term_counts = Counter(
        query_terms
    )

    document_count = bm25_index["document_count"]
    average_length = bm25_index["average_length"]
    document_frequency = bm25_index["document_frequency"]
    tokenized_documents = bm25_index["tokens"]

    k1 = 1.2
    b = 0.75

    ranked_chunks = []

    for chunk in chunks:
        tokens = tokenized_documents[chunk.chunk_id]
        term_frequency = Counter(
            tokens
        )
        document_length = len(tokens)
        score = 0.0

        for term, query_frequency in query_term_counts.items():
            if term_frequency[term] == 0:
                continue

            idf = math.log(
                1
                + (
                    document_count
                    - document_frequency[term]
                    + 0.5
                )
                / (
                    document_frequency[term]
                    + 0.5
                )
            )

            denominator = (
                term_frequency[term]
                + k1
                * (
                    1
                    - b
                    + b
                    * document_length
                    / average_length
                )
            )

            score += (
                idf
                * term_frequency[term]
                * (
                    k1
                    + 1
                )
                / denominator
                * query_frequency
            )

        ranked_chunk = clone_chunk(
            chunk
        )
        ranked_chunk.lexical_score = score
        ranked_chunks.append(
            ranked_chunk
        )

    ranked_chunks.sort(
        key=lambda item: (
            item.lexical_score,
            -item.chunk_id
        ),
        reverse=True
    )

    return ranked_chunks


def reciprocal_rank_fusion(ranked_lists, rrf_k=RRF_K):
    by_chunk_id = {}
    fused_scores = Counter()

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(
            ranked_list,
            start=1
        ):
            by_chunk_id[chunk.chunk_id] = chunk
            fused_scores[chunk.chunk_id] += (
                1.0
                / (
                    rrf_k
                    + rank
                )
            )

    fused_chunks = []

    for chunk_id, score in fused_scores.items():
        chunk = clone_chunk(
            by_chunk_id[chunk_id]
        )
        chunk.fused_score = score
        fused_chunks.append(
            chunk
        )

    fused_chunks.sort(
        key=lambda item: (
            item.fused_score,
            item.dense_score
            if item.dense_score is not None
            else float("-inf"),
            item.lexical_score,
            -item.chunk_id
        ),
        reverse=True
    )

    return fused_chunks


def load_cross_encoder():
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(
        model_name=RERANKER_MODEL_NAME
    )


def rerank_chunks(question, chunks, cross_encoder):
    rerank_start = time.perf_counter()
    documents = [
        "\n".join(
            [
                chunk.title,
                chunk.topic,
                chunk.chunk_text
            ]
        )
        for chunk in chunks
    ]
    scores = list(
        cross_encoder.rerank(
            question,
            documents,
            batch_size=RERANK_BATCH_SIZE
        )
    )
    rerank_ms = (
        time.perf_counter() - rerank_start
    ) * 1000

    reranked_chunks = []

    for chunk, score in zip(
        chunks,
        scores
    ):
        reranked_chunk = clone_chunk(
            chunk
        )
        reranked_chunk.rerank_score = float(
            score
        )
        reranked_chunks.append(
            reranked_chunk
        )

    reranked_chunks.sort(
        key=lambda item: (
            item.rerank_score
            if item.rerank_score is not None
            else float("-inf"),
            item.fused_score,
            item.dense_score
            if item.dense_score is not None
            else float("-inf"),
            item.lexical_score,
            -item.chunk_id
        ),
        reverse=True
    )

    return (
        reranked_chunks,
        rerank_ms
    )


def dedupe_document_ranking(chunks, score_field):
    document_ranking = []
    seen_documents = set()

    for chunk in chunks:
        if chunk.document_id in seen_documents:
            continue

        seen_documents.add(
            chunk.document_id
        )

        score = getattr(
            chunk,
            score_field
        )

        document_ranking.append(
            {
                "document_id": chunk.document_id,
                "title": chunk.title,
                "score": (
                    float(score)
                    if score is not None
                    else 0.0
                ),
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index
            }
        )

    return document_ranking


def find_expected_rank(document_ranking, expected_document):
    if not expected_document:
        return None

    for rank, result in enumerate(
        document_ranking,
        start=1
    ):
        if result["document_id"] == expected_document:
            return rank

    return None


def expected_document_in_candidate_pool(item, chunks):
    expected_document = item["EXPECTED_DOCUMENT_ID"].strip()

    if (
        not is_supported(item)
        or not expected_document
    ):
        return ""

    return int(
        any(
            chunk.document_id == expected_document
            for chunk in chunks
        )
    )


def candidate_pool_documents(item, chunks):
    if not is_supported(item):
        return ""

    documents = []
    seen_documents = set()

    for chunk in chunks:
        if chunk.document_id in seen_documents:
            continue

        seen_documents.add(
            chunk.document_id
        )
        documents.append(
            chunk.document_id
        )

    return ";".join(
        documents
    )


def evaluate_variant_result(
    item,
    variant,
    document_ranking,
    latency_ms,
    embedding_ms=0.0,
    dense_hana_ms=0.0,
    lexical_ms=0.0,
    rerank_ms=0.0,
    candidate_chunks=None
):
    expected_document = item["EXPECTED_DOCUMENT_ID"].strip()
    expected_rank = find_expected_rank(
        document_ranking,
        expected_document
    )

    if is_supported(item):
        reciprocal_rank = (
            1.0 / expected_rank
            if expected_rank is not None
            else 0.0
        )
        top1 = expected_rank == 1
        top3 = (
            expected_rank is not None
            and expected_rank <= 3
        )
        top5 = (
            expected_rank is not None
            and expected_rank <= 5
        )
    else:
        reciprocal_rank = 0.0
        top1 = False
        top3 = False
        top5 = False

    rank1 = (
        document_ranking[0]
        if len(document_ranking) >= 1
        else None
    )
    rank2 = (
        document_ranking[1]
        if len(document_ranking) >= 2
        else None
    )

    rank1_score = (
        rank1["score"]
        if rank1
        else None
    )
    rank2_score = (
        rank2["score"]
        if rank2
        else None
    )

    margin = (
        rank1_score - rank2_score
        if (
            rank1_score is not None
            and rank2_score is not None
        )
        else None
    )

    return {
        "VARIANT":
            variant.key,
        "VARIANT_LABEL":
            variant.label,
        "QUERY_ID":
            item["QUERY_ID"],
        "EXPECTED_SUPPORTED":
            item["EXPECTED_SUPPORTED"].strip(),
        "EXPECTED_DOCUMENT_ID":
            expected_document,
        "CATEGORY":
            item["CATEGORY"],
        "EXPECTED_RANK":
            (
                expected_rank
                if expected_rank is not None
                else 0
            ),
        "RANK1_DOCUMENT_ID":
            (
                rank1["document_id"]
                if rank1
                else ""
            ),
        "RANK1_SCORE":
            (
                round(rank1_score, 4)
                if rank1_score is not None
                else ""
            ),
        "RANK2_DOCUMENT_ID":
            (
                rank2["document_id"]
                if rank2
                else ""
            ),
        "RANK2_SCORE":
            (
                round(rank2_score, 4)
                if rank2_score is not None
                else ""
            ),
        "RANK1_RANK2_MARGIN":
            (
                round(margin, 4)
                if margin is not None
                else ""
            ),
        "TOP5_DOCUMENTS":
            ";".join(
                result["document_id"]
                for result in document_ranking[:5]
            ),
        "TOP1_CORRECT":
            int(top1),
        "TOP3_CORRECT":
            int(top3),
        "TOP5_CORRECT":
            int(top5),
        "RECIPROCAL_RANK":
            round(
                reciprocal_rank,
                4
            ),
        "LATENCY_MS":
            round(
                latency_ms,
                2
            ),
        "EMBEDDING_MS":
            round(
                embedding_ms,
                2
            ),
        "DENSE_HANA_MS":
            round(
                dense_hana_ms,
                2
            ),
        "LEXICAL_MS":
            round(
                lexical_ms,
                2
            ),
        "RERANK_MS":
            round(
                rerank_ms,
                2
            ),
        "CANDIDATE_EXPECTED_PRESENT":
            expected_document_in_candidate_pool(
                item,
                candidate_chunks or []
            ),
        "CANDIDATE_POOL_DOCUMENTS":
            candidate_pool_documents(
                item,
                candidate_chunks or []
            )
    }


def summarize_variant(results, variant):
    supported_results = [
        result
        for result in results
        if (
            result["VARIANT"] == variant.key
            and result["EXPECTED_SUPPORTED"] == "1"
        )
    ]

    total = len(
        supported_results
    )

    top1 = sum(
        result["TOP1_CORRECT"]
        for result in supported_results
    )
    top3 = sum(
        result["TOP3_CORRECT"]
        for result in supported_results
    )
    top5 = sum(
        result["TOP5_CORRECT"]
        for result in supported_results
    )
    reciprocal_rank_sum = sum(
        result["RECIPROCAL_RANK"]
        for result in supported_results
    )
    latency_values = [
        result["LATENCY_MS"]
        for result in results
        if result["VARIANT"] == variant.key
    ]
    rerank_values = [
        result["RERANK_MS"]
        for result in results
        if result["VARIANT"] == variant.key
    ]

    return {
        "VARIANT": variant.key,
        "VARIANT_LABEL": variant.label,
        "SUPPORTED_TOTAL": total,
        "TOP1_ACCURACY": (
            top1 / total
            if total
            else 0.0
        ),
        "TOP1_COUNT": top1,
        "TOP3_ACCURACY": (
            top3 / total
            if total
            else 0.0
        ),
        "TOP3_COUNT": top3,
        "TOP5_ACCURACY": (
            top5 / total
            if total
            else 0.0
        ),
        "TOP5_COUNT": top5,
        "MRR": (
            reciprocal_rank_sum / total
            if total
            else 0.0
        ),
        "MEAN_LATENCY_MS": (
            sum(latency_values) / len(latency_values)
            if latency_values
            else 0.0
        ),
        "MEAN_RERANK_MS": (
            sum(rerank_values) / len(rerank_values)
            if rerank_values
            else 0.0
        )
    }


def compare_to_dense_baseline(results):
    dense_ranks = {
        result["QUERY_ID"]: result["EXPECTED_RANK"]
        for result in results
        if result["VARIANT"] == "A"
    }

    comparisons = []

    for result in results:
        if result["VARIANT"] == "A":
            continue

        baseline_rank = dense_ranks.get(
            result["QUERY_ID"],
            0
        )
        variant_rank = result["EXPECTED_RANK"]

        if baseline_rank == 0 and variant_rank == 0:
            movement = 0
        elif baseline_rank == 0:
            movement = 999
        elif variant_rank == 0:
            movement = -999
        else:
            movement = baseline_rank - variant_rank

        comparisons.append(
            {
                "VARIANT": result["VARIANT"],
                "QUERY_ID": result["QUERY_ID"],
                "EXPECTED_SUPPORTED": result["EXPECTED_SUPPORTED"],
                "BASELINE_EXPECTED_RANK": baseline_rank,
                "VARIANT_EXPECTED_RANK": variant_rank,
                "RANK_MOVEMENT": movement,
                "BASELINE_TOP5_DOCUMENTS":
                    next(
                        item["TOP5_DOCUMENTS"]
                        for item in results
                        if (
                            item["VARIANT"] == "A"
                            and item["QUERY_ID"] == result["QUERY_ID"]
                        )
                    ),
                "VARIANT_TOP5_DOCUMENTS": result["TOP5_DOCUMENTS"]
            }
        )

    return comparisons


def print_variant_summaries(results):
    print()
    print("=" * 90)
    print("SUPPORTED QUESTION METRICS BY VARIANT")
    print("=" * 90)
    print(
        "VARIANT,"
        "VARIANT_LABEL,"
        "SUPPORTED_TOTAL,"
        "TOP1_ACCURACY,"
        "TOP1_COUNT,"
        "TOP3_ACCURACY,"
        "TOP3_COUNT,"
        "TOP5_ACCURACY,"
        "TOP5_COUNT,"
        "MRR,"
        "MEAN_LATENCY_MS,"
        "MEAN_RERANK_MS"
    )

    for variant in VARIANTS:
        summary = summarize_variant(
            results,
            variant
        )
        print(
            f"{summary['VARIANT']},"
            f"{summary['VARIANT_LABEL']},"
            f"{summary['SUPPORTED_TOTAL']},"
            f"{summary['TOP1_ACCURACY']:.4f},"
            f"{summary['TOP1_COUNT']},"
            f"{summary['TOP3_ACCURACY']:.4f},"
            f"{summary['TOP3_COUNT']},"
            f"{summary['TOP5_ACCURACY']:.4f},"
            f"{summary['TOP5_COUNT']},"
            f"{summary['MRR']:.4f},"
            f"{summary['MEAN_LATENCY_MS']:.2f},"
            f"{summary['MEAN_RERANK_MS']:.2f}"
        )


def print_detailed_results(results):
    print()
    print("=" * 90)
    print("DETAILED VARIANT RESULTS")
    print("=" * 90)
    print(
        "VARIANT,"
        "VARIANT_LABEL,"
        "QUERY_ID,"
        "EXPECTED_SUPPORTED,"
        "EXPECTED_DOCUMENT_ID,"
        "CATEGORY,"
        "EXPECTED_RANK,"
        "RANK1_DOCUMENT_ID,"
        "RANK1_SCORE,"
        "RANK2_DOCUMENT_ID,"
        "RANK2_SCORE,"
        "RANK1_RANK2_MARGIN,"
        "TOP5_DOCUMENTS,"
        "TOP1_CORRECT,"
        "TOP3_CORRECT,"
        "TOP5_CORRECT,"
        "RECIPROCAL_RANK,"
        "LATENCY_MS,"
        "EMBEDDING_MS,"
        "DENSE_HANA_MS,"
        "LEXICAL_MS,"
        "RERANK_MS,"
        "CANDIDATE_EXPECTED_PRESENT,"
        "CANDIDATE_POOL_DOCUMENTS"
    )

    for result in results:
        print(
            f"{result['VARIANT']},"
            f"{result['VARIANT_LABEL']},"
            f"{result['QUERY_ID']},"
            f"{result['EXPECTED_SUPPORTED']},"
            f"{result['EXPECTED_DOCUMENT_ID']},"
            f"{result['CATEGORY']},"
            f"{result['EXPECTED_RANK']},"
            f"{result['RANK1_DOCUMENT_ID']},"
            f"{result['RANK1_SCORE']},"
            f"{result['RANK2_DOCUMENT_ID']},"
            f"{result['RANK2_SCORE']},"
            f"{result['RANK1_RANK2_MARGIN']},"
            f"{result['TOP5_DOCUMENTS']},"
            f"{result['TOP1_CORRECT']},"
            f"{result['TOP3_CORRECT']},"
            f"{result['TOP5_CORRECT']},"
            f"{result['RECIPROCAL_RANK']},"
            f"{result['LATENCY_MS']},"
            f"{result['EMBEDDING_MS']},"
            f"{result['DENSE_HANA_MS']},"
            f"{result['LEXICAL_MS']},"
            f"{result['RERANK_MS']},"
            f"{result['CANDIDATE_EXPECTED_PRESENT']},"
            f"{result['CANDIDATE_POOL_DOCUMENTS']}"
        )


def print_baseline_comparison(results):
    print()
    print("=" * 90)
    print("PER-QUERY MOVEMENT RELATIVE TO DENSE BASELINE")
    print("=" * 90)
    print(
        "VARIANT,"
        "QUERY_ID,"
        "EXPECTED_SUPPORTED,"
        "BASELINE_EXPECTED_RANK,"
        "VARIANT_EXPECTED_RANK,"
        "RANK_MOVEMENT,"
        "BASELINE_TOP5_DOCUMENTS,"
        "VARIANT_TOP5_DOCUMENTS"
    )

    for item in compare_to_dense_baseline(
        results
    ):
        print(
            f"{item['VARIANT']},"
            f"{item['QUERY_ID']},"
            f"{item['EXPECTED_SUPPORTED']},"
            f"{item['BASELINE_EXPECTED_RANK']},"
            f"{item['VARIANT_EXPECTED_RANK']},"
            f"{item['RANK_MOVEMENT']},"
            f"{item['BASELINE_TOP5_DOCUMENTS']},"
            f"{item['VARIANT_TOP5_DOCUMENTS']}"
        )


def print_candidate_recall_diagnostics(results):
    print()
    print("=" * 90)
    print("SUPPORTED CANDIDATE RECALL BEFORE RERANKING")
    print("=" * 90)
    print(
        "VARIANT,"
        "QUERY_ID,"
        "EXPECTED_DOCUMENT_ID,"
        "CANDIDATE_EXPECTED_PRESENT,"
        "CANDIDATE_POOL_DOCUMENTS"
    )

    reranking_variants = {
        "C",
        "D"
    }
    diagnostic_results = [
        result
        for result in results
        if (
            result["VARIANT"] in reranking_variants
            and result["EXPECTED_SUPPORTED"] == "1"
        )
    ]

    for result in diagnostic_results:
        print(
            f"{result['VARIANT']},"
            f"{result['QUERY_ID']},"
            f"{result['EXPECTED_DOCUMENT_ID']},"
            f"{result['CANDIDATE_EXPECTED_PRESENT']},"
            f"{result['CANDIDATE_POOL_DOCUMENTS']}"
        )

    print()
    print("CANDIDATE_RECALL_SUMMARY")
    print(
        "VARIANT,"
        "SUPPORTED_TOTAL,"
        "EXPECTED_PRESENT_COUNT,"
        "EXPECTED_PRESENT_RATE"
    )

    for variant in [
        "C",
        "D"
    ]:
        variant_results = [
            result
            for result in diagnostic_results
            if result["VARIANT"] == variant
        ]
        total = len(
            variant_results
        )
        present_count = sum(
            int(
                result["CANDIDATE_EXPECTED_PRESENT"]
            )
            for result in variant_results
        )
        present_rate = (
            present_count / total
            if total
            else 0.0
        )
        print(
            f"{variant},"
            f"{total},"
            f"{present_count},"
            f"{present_rate:.4f}"
        )


def main():
    queries = load_queries()

    print()
    print("SAP BTP Documentation Assistant")
    print("Version 2 Retrieval Ranking Variant Experiment")
    print("=" * 90)
    print("Calibration file:", CALIBRATION_FILE)
    print("Target table:", TABLE_NAME)
    print("Dense embedding model:", MODEL_NAME)
    print("Cross-encoder reranker:", RERANKER_MODEL_NAME)
    print("Dense candidate chunks:", DENSE_CANDIDATE_CHUNKS)
    print("Lexical candidate chunks:", LEXICAL_CANDIDATE_CHUNKS)
    print("RRF k:", RRF_K)
    print("Questions:", len(queries))
    print(
        "This script is read-only to HANA and does not modify "
        "the production search behavior in app.py."
    )

    corpus_chunks, corpus_hana_ms = fetch_corpus_chunks()
    print(
        "Corpus chunks loaded:",
        len(corpus_chunks),
        f"({corpus_hana_ms:.2f} ms one-time read)"
    )
    bm25_index = build_bm25_index(
        corpus_chunks
    )
    cross_encoder = load_cross_encoder()

    results = []

    for item in queries:
        question = item["QUESTION"]

        dense_chunks, embedding_ms, dense_hana_ms = fetch_dense_chunks(
            question
        )
        lexical_start = time.perf_counter()
        lexical_chunks = bm25_rank(
            question,
            corpus_chunks,
            bm25_index
        )
        lexical_ms = (
            time.perf_counter() - lexical_start
        ) * 1000

        dense_candidate_chunks = dense_chunks[
            :DENSE_CANDIDATE_CHUNKS
        ]
        lexical_candidate_chunks = lexical_chunks[
            :LEXICAL_CANDIDATE_CHUNKS
        ]

        dense_ranking = dedupe_document_ranking(
            dense_chunks,
            "dense_score"
        )
        results.append(
            evaluate_variant_result(
                item,
                VARIANTS[0],
                dense_ranking,
                embedding_ms + dense_hana_ms,
                embedding_ms=embedding_ms,
                dense_hana_ms=dense_hana_ms
            )
        )

        hybrid_chunks = reciprocal_rank_fusion(
            [
                dense_chunks,
                lexical_chunks
            ]
        )
        hybrid_ranking = dedupe_document_ranking(
            hybrid_chunks,
            "fused_score"
        )
        results.append(
            evaluate_variant_result(
                item,
                VARIANTS[1],
                hybrid_ranking,
                embedding_ms + dense_hana_ms + lexical_ms,
                embedding_ms=embedding_ms,
                dense_hana_ms=dense_hana_ms,
                lexical_ms=lexical_ms
            )
        )

        dense_reranked_chunks, dense_rerank_ms = rerank_chunks(
            question,
            dense_candidate_chunks,
            cross_encoder
        )
        dense_reranked_ranking = dedupe_document_ranking(
            dense_reranked_chunks,
            "rerank_score"
        )
        results.append(
            evaluate_variant_result(
                item,
                VARIANTS[2],
                dense_reranked_ranking,
                embedding_ms + dense_hana_ms + dense_rerank_ms,
                embedding_ms=embedding_ms,
                dense_hana_ms=dense_hana_ms,
                rerank_ms=dense_rerank_ms,
                candidate_chunks=dense_candidate_chunks
            )
        )

        hybrid_candidate_chunks = reciprocal_rank_fusion(
            [
                dense_candidate_chunks,
                lexical_candidate_chunks
            ]
        )
        hybrid_reranked_chunks, hybrid_rerank_ms = rerank_chunks(
            question,
            hybrid_candidate_chunks,
            cross_encoder
        )
        hybrid_reranked_ranking = dedupe_document_ranking(
            hybrid_reranked_chunks,
            "rerank_score"
        )
        results.append(
            evaluate_variant_result(
                item,
                VARIANTS[3],
                hybrid_reranked_ranking,
                (
                    embedding_ms
                    + dense_hana_ms
                    + lexical_ms
                    + hybrid_rerank_ms
                ),
                embedding_ms=embedding_ms,
                dense_hana_ms=dense_hana_ms,
                lexical_ms=lexical_ms,
                rerank_ms=hybrid_rerank_ms,
                candidate_chunks=hybrid_candidate_chunks
            )
        )

        print(
            f"{item['QUERY_ID']:<8} "
            f"A={results[-4]['EXPECTED_RANK']:<3} "
            f"B={results[-3]['EXPECTED_RANK']:<3} "
            f"C={results[-2]['EXPECTED_RANK']:<3} "
            f"D={results[-1]['EXPECTED_RANK']:<3} "
            f"Top5A={results[-4]['TOP5_DOCUMENTS']} "
            f"Top5D={results[-1]['TOP5_DOCUMENTS']}"
        )

    print_variant_summaries(
        results
    )
    print_detailed_results(
        results
    )
    print_candidate_recall_diagnostics(
        results
    )
    print_baseline_comparison(
        results
    )


if __name__ == "__main__":
    main()
