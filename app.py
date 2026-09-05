import html
import json
import os
import re

from flask import Flask, request, render_template, render_template_string
from fastembed import TextEmbedding
from hdbcli import dbapi
from markupsafe import Markup


app = Flask(__name__)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

MODEL_NAME = "BAAI/bge-small-en-v1.5"
HDI_SERVICE_NAME = "btp-doc-assistant-hdi"

_embedding_model = None


# ---------------------------------------------------------------------
# Embedding Model
# ---------------------------------------------------------------------

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = TextEmbedding(
            model_name=MODEL_NAME
        )

    return _embedding_model


# ---------------------------------------------------------------------
# SAP HANA / HDI Connection
# ---------------------------------------------------------------------

def get_hana_credentials():
    raw_services = os.environ.get("VCAP_SERVICES")

    if not raw_services:
        raise RuntimeError(
            "VCAP_SERVICES is not available. "
            "The application must run in SAP BTP Cloud Foundry "
            "with the HDI service bound."
        )

    services = json.loads(raw_services)

    hana_services = services.get("hana", [])

    for service in hana_services:
        if service.get("name") == HDI_SERVICE_NAME:
            credentials = service.get("credentials", {})

            required_fields = [
                "host",
                "port",
                "user",
                "password"
            ]

            missing = [
                field
                for field in required_fields
                if not credentials.get(field)
            ]

            if missing:
                raise RuntimeError(
                    "Required HANA credentials are missing: "
                    + ", ".join(missing)
                )

            return credentials

    raise RuntimeError(
        f"HDI service '{HDI_SERVICE_NAME}' "
        "was not found in VCAP_SERVICES."
    )


def get_hana_connection():
    credentials = get_hana_credentials()

    connection = dbapi.connect(
        address=credentials["host"],
        port=int(credentials["port"]),
        user=credentials["user"],
        password=credentials["password"]
    )

    schema = credentials.get("schema")

    if not schema:
        connection.close()

        raise RuntimeError(
            "HDI container schema is missing "
            "from the service binding."
        )

    cursor = connection.cursor()

    try:
        cursor.execute(
            f'SET SCHEMA "{schema}"'
        )
    finally:
        cursor.close()

    return connection


# ---------------------------------------------------------------------
# Vector Helpers
# ---------------------------------------------------------------------

def vector_to_string(vector):
    return json.dumps(
        [
            float(value)
            for value in vector
        ]
    )


# ---------------------------------------------------------------------
# Semantic Search
# ---------------------------------------------------------------------

def semantic_search(question, top_k=5):
    top_k = max(
        1,
        min(int(top_k), 10)
    )

    model = get_embedding_model()

    query_vector = list(
        model.query_embed(
            [question]
        )
    )[0]

    connection = get_hana_connection()
    cursor = connection.cursor()

    try:
        sql = f"""
            SELECT TOP {top_k}
                "DOCUMENT_ID",
                "TITLE",
                "TOPIC",
                "SOURCE_URL",
                "CHUNK_TEXT",
                COSINE_SIMILARITY(
                    "EMBEDDING",
                    TO_REAL_VECTOR(?)
                ) AS "SCORE"
            FROM "DOCUMENT_CHUNKS_V2"
            WHERE "EMBEDDING" IS NOT NULL
            ORDER BY "SCORE" DESC
        """

        cursor.execute(
            sql,
            (
                vector_to_string(
                    query_vector
                ),
            )
        )

        rows = cursor.fetchall()

        results = []

        for row in rows:
            results.append(
                {
                    "document_id": row[0],
                    "title": row[1],
                    "topic": row[2],
                    "source_url": row[3],
                    "chunk_text": row[4],
                    "score": float(row[5])
                }
            )

        return results

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------
# Main User Interface
# ---------------------------------------------------------------------

_CITATION_PATTERN = re.compile(
    r"\[(DOC\d+)\]\((https://[^)\s]+)\)"
)


def render_answer_html(answer):
    answer = str(
        answer or ""
    )

    rendered = []
    position = 0

    for match in _CITATION_PATTERN.finditer(
        answer
    ):
        plain_text = answer[
            position:match.start()
        ]

        escaped = html.escape(
            plain_text
        ).replace(
            "\n",
            "<br>"
        )

        escaped = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            escaped
        )

        rendered.append(
            escaped
        )

        document_id = html.escape(
            match.group(1)
        )
        source_url = html.escape(
            match.group(2),
            quote=True
        )

        rendered.append(
            f'<a href="{source_url}" '
            f'target="_blank" '
            f'rel="noopener noreferrer">'
            f'{document_id}</a>'
        )

        position = match.end()

    remaining = html.escape(
        answer[position:]
    ).replace(
        "\n",
        "<br>"
    )

    remaining = re.sub(
        r"\*\*(.+?)\*\*",
        r"<strong>\1</strong>",
        remaining
    )

    rendered.append(
        remaining
    )

    return Markup(
        "".join(
            rendered
        )
    )


@app.route("/", methods=["GET", "POST"])
def home():
    question = ""
    result = None
    sources = []
    answer_html = ""
    error = None

    if request.method == "POST":
        question = request.form.get(
            "question",
            ""
        ).strip()

        if question:
            try:
                # Lazy import avoids circular imports because the
                # frozen retrieval evaluator imports shared helpers
                # from this application module.
                from rag_pipeline import (
                    answer_documentation_question
                )

                result = (
                    answer_documentation_question(
                        question
                    )
                )

                if result["OUTCOME"] == "PROVIDER_ERROR":
                    error = result.get(
                        "PROVIDER_ERROR"
                    ) or "LLM provider error."

                answer_html = render_answer_html(
                    result.get(
                        "ANSWER",
                        ""
                    )
                )

                sources = result.get(
                    "SOURCES",
                    []
                )

            except Exception as exc:
                error = str(
                    exc
                )

    return render_template(
        "index.html",
        question=question,
        result=result,
        answer_html=answer_html,
        sources=sources,
        error=error
    )


# ---------------------------------------------------------------------
# Technical Validation Routes
# ---------------------------------------------------------------------

@app.route("/db-test")
def db_test():
    connection = None
    cursor = None

    try:
        connection = get_hana_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT CURRENT_UTCTIMESTAMP FROM DUMMY"
        )

        result = cursor.fetchone()

        timestamp = result[0]

        return f"""
        <html>
        <body>
            <h1>HANA Connection Successful</h1>

            <p>
                The SAP BTP Cloud Foundry application
                successfully connected to SAP HANA Cloud
                through the HDI service binding.
            </p>

            <p>
                Database UTC timestamp:
                {html.escape(str(timestamp))}
            </p>

            <p>
                <a href="/">Back to Documentation Assistant</a>
            </p>
        </body>
        </html>
        """

    except Exception as exc:
        return f"""
        <html>
        <body>
            <h1>HANA Connection Failed</h1>

            <pre>
{html.escape(str(exc))}
            </pre>

            <p>
                <a href="/">Back</a>
            </p>
        </body>
        </html>
        """, 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@app.route("/embedding-test")
def embedding_test():
    try:
        question = (
            "How can a Cloud Foundry application "
            "connect to SAP HANA Cloud?"
        )

        model = get_embedding_model()

        vector = list(
            model.query_embed(
                [question]
            )
        )[0]

        return f"""
        <html>
        <body>

            <h1>Embedding Test Successful</h1>

            <p>
                <strong>Model:</strong>
                {html.escape(MODEL_NAME)}
            </p>

            <p>
                <strong>Vector dimension:</strong>
                {len(vector)}
            </p>

            <p>
                <strong>Execution environment:</strong>
                SAP BTP Cloud Foundry
            </p>

            <p>
                <a href="/">Back to Documentation Assistant</a>
            </p>

        </body>
        </html>
        """

    except Exception as exc:
        return f"""
        <html>
        <body>

            <h1>Embedding Test Failed</h1>

            <pre>
{html.escape(str(exc))}
            </pre>

            <p>
                <a href="/">Back</a>
            </p>

        </body>
        </html>
        """, 500


@app.route("/table-test")
def table_test():
    connection = None
    cursor = None

    try:
        connection = get_hana_connection()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT COUNT(*) '
            'FROM "DOCUMENT_CHUNKS_V2"'
        )

        row_count = cursor.fetchone()[0]

        return f"""
        <html>
        <body>

            <h1>DOCUMENT_CHUNKS_V2 Accessible</h1>

            <p>
                Rows:
                <strong>
                    {html.escape(str(row_count))}
                </strong>
            </p>

            <p>
                The Flask application can access the
                HDI-managed SAP HANA Cloud table.
            </p>

            <p>
                <a href="/">Back to Documentation Assistant</a>
            </p>

        </body>
        </html>
        """

    except Exception as exc:
        return f"""
        <html>
        <body>

            <h1>DOCUMENT_CHUNKS_V2 Test Failed</h1>

            <pre>
{html.escape(str(exc))}
            </pre>

            <p>
                <a href="/">Back</a>
            </p>

        </body>
        </html>
        """, 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ---------------------------------------------------------------------
# Local Development
# ---------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )