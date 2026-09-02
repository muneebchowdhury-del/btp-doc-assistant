import unittest
from types import SimpleNamespace

from rag_context import (
    RAG_CONTEXT_FIELDS,
    RAG_CONTEXT_LIMIT,
    build_rag_contexts_from_hybrid_results
)


def chunk(document_id, chunk_id, rank_text=None):
    return SimpleNamespace(
        chunk_id=chunk_id,
        document_id=document_id,
        title=f"{document_id} title",
        source_url=f"https://help.sap.com/docs/example/{document_id.lower()}",
        chunk_text=rank_text or f"{document_id} chunk {chunk_id}"
    )


class RAGContextTests(unittest.TestCase):
    def test_selects_top_five_unique_documents(self):
        contexts = build_rag_contexts_from_hybrid_results(
            [
                chunk("DOC001", 1),
                chunk("DOC002", 2),
                chunk("DOC003", 3),
                chunk("DOC004", 4),
                chunk("DOC005", 5),
                chunk("DOC006", 6)
            ]
        )

        self.assertEqual(
            RAG_CONTEXT_LIMIT,
            len(
                contexts
            )
        )
        self.assertEqual(
            [
                "DOC001",
                "DOC002",
                "DOC003",
                "DOC004",
                "DOC005"
            ],
            [
                context["document_id"]
                for context in contexts
            ]
        )

    def test_duplicate_chunks_collapse_to_highest_ranked_document_chunk(self):
        contexts = build_rag_contexts_from_hybrid_results(
            [
                chunk(
                    "DOC001",
                    2,
                    "highest-ranked fused chunk"
                ),
                chunk(
                    "DOC002",
                    3
                ),
                chunk(
                    "DOC001",
                    1,
                    "lower-ranked duplicate chunk"
                )
            ]
        )

        self.assertEqual(
            [
                "DOC001",
                "DOC002"
            ],
            [
                context["document_id"]
                for context in contexts
            ]
        )
        self.assertEqual(
            "highest-ranked fused chunk",
            contexts[0]["chunk_text"]
        )

    def test_preserves_document_level_retrieval_order(self):
        contexts = build_rag_contexts_from_hybrid_results(
            [
                chunk("DOC009", 9),
                chunk("DOC003", 3),
                chunk("DOC007", 7)
            ]
        )

        self.assertEqual(
            [
                ("DOC009", 1),
                ("DOC003", 2),
                ("DOC007", 3)
            ],
            [
                (
                    context["document_id"],
                    context["retrieval_rank"]
                )
                for context in contexts
            ]
        )

    def test_contexts_have_exact_required_fields(self):
        contexts = build_rag_contexts_from_hybrid_results(
            [
                chunk("DOC001", 1)
            ]
        )

        self.assertEqual(
            set(
                RAG_CONTEXT_FIELDS
            ),
            set(
                contexts[0].keys()
            )
        )

    def test_handles_fewer_than_five_documents(self):
        contexts = build_rag_contexts_from_hybrid_results(
            [
                chunk("DOC001", 1),
                chunk("DOC002", 2)
            ]
        )

        self.assertEqual(
            2,
            len(
                contexts
            )
        )

    def test_repeated_execution_is_deterministic(self):
        hybrid_chunks = [
            chunk("DOC001", 1),
            chunk("DOC002", 2),
            chunk("DOC001", 3),
            chunk("DOC003", 4)
        ]

        first = build_rag_contexts_from_hybrid_results(
            hybrid_chunks
        )
        second = build_rag_contexts_from_hybrid_results(
            hybrid_chunks
        )

        self.assertEqual(
            first,
            second
        )


if __name__ == "__main__":
    unittest.main()
