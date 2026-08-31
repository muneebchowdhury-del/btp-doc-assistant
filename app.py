import html
import json
import os

from flask import Flask, request, render_template_string
from fastembed import TextEmbedding
from hdbcli import dbapi


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
            FROM "DOCUMENT_CHUNKS"
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

@app.route("/", methods=["GET", "POST"])
def home():
    question = ""
    results = []
    error = None

    if request.method == "POST":
        question = request.form.get(
            "question",
            ""
        ).strip()

        if question:
            try:
                results = semantic_search(
                    question,
                    top_k=5
                )

            except Exception as exc:
                error = str(exc)

    return render_template_string(
        """
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>
        SAP BTP Documentation Assistant
    </title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family:
                Arial,
                Helvetica,
                sans-serif;
            background: #f5f6f7;
            color: #222;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 50px 25px;
        }

        .header {
            margin-bottom: 35px;
        }

        h1 {
            margin-bottom: 8px;
            font-size: 32px;
        }

        .subtitle {
            color: #666;
            font-size: 16px;
        }

        .search-box {
            background: white;
            padding: 22px;
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-bottom: 30px;
        }

        form {
            display: flex;
            gap: 12px;
        }

        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 1px solid #bbb;
            border-radius: 7px;
            font-size: 16px;
        }

        input[type="text"]:focus {
            outline: 2px solid #999;
        }

        button {
            border: none;
            border-radius: 7px;
            padding: 15px 25px;
            font-size: 16px;
            cursor: pointer;
            background: #222;
            color: white;
        }

        button:hover {
            opacity: 0.88;
        }

        .question {
            margin-bottom: 20px;
            color: #555;
        }

        .result {
            background: white;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 22px;
            margin-bottom: 18px;
        }

        .result h3 {
            margin-top: 0;
            margin-bottom: 8px;
        }

        .metadata {
            font-size: 14px;
            color: #666;
            margin-bottom: 6px;
        }

        .score {
            display: inline-block;
            margin-top: 4px;
            margin-bottom: 15px;
            padding: 5px 9px;
            background: #f1f1f1;
            border-radius: 5px;
            font-size: 13px;
        }

        .passage {
            line-height: 1.6;
            margin-bottom: 16px;
        }

        .source a {
            text-decoration: none;
            font-weight: bold;
        }

        .source a:hover {
            text-decoration: underline;
        }

        .error {
            background: #fff1f1;
            border: 1px solid #e0aaaa;
            padding: 15px;
            border-radius: 7px;
            margin-bottom: 25px;
        }

        .empty {
            background: white;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }

        .technical-links {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 13px;
            color: #777;
        }

        .technical-links a {
            margin-right: 15px;
        }

        @media (max-width: 700px) {

            form {
                flex-direction: column;
            }

            button {
                width: 100%;
            }

        }

    </style>

</head>


<body>

<div class="container">

    <div class="header">

        <h1>
            SAP BTP Documentation Assistant
        </h1>

        <div class="subtitle">
            Semantic search across selected official
            SAP BTP documentation
        </div>

    </div>


    <div class="search-box">

        <form method="POST">

            <input
                type="text"
                name="question"
                value="{{ question }}"
                placeholder="Ask a question about SAP BTP..."
                required
            >

            <button type="submit">
                Search
            </button>

        </form>

    </div>


    {% if error %}

        <div class="error">
            <strong>Search error:</strong>
            {{ error }}
        </div>

    {% endif %}


    {% if question and not error %}

        <div class="question">
            Results for:
            <strong>{{ question }}</strong>
        </div>

    {% endif %}


    {% if results %}

        <h2>
            Top Semantic Results
        </h2>


        {% for result in results %}

            <div class="result">

                <h3>
                    {{ loop.index }}.
                    {{ result.title }}
                </h3>


                <div class="metadata">

                    Topic:
                    {{ result.topic }}

                    &nbsp;·&nbsp;

                    Document:
                    {{ result.document_id }}

                </div>


                <div class="score">

                    Similarity:
                    {{ "%.4f"|format(result.score) }}

                </div>


                <div class="passage">

                    {{ result.chunk_text }}

                </div>


                <div class="source">

                    <a
                        href="{{ result.source_url }}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Open official SAP source ↗
                    </a>

                </div>

            </div>

        {% endfor %}


    {% elif question and not error %}

        <div class="empty">
            No matching documentation passages were found.
        </div>

    {% endif %}


    <div class="technical-links">

        Technical validation:

        <a href="/db-test">
            HANA Connection
        </a>

        <a href="/embedding-test">
            Embedding Model
        </a>

        <a href="/table-test">
            Documentation Table
        </a>

    </div>

</div>

</body>

</html>
        """,
        question=question,
        results=results,
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
            'FROM "DOCUMENT_CHUNKS"'
        )

        row_count = cursor.fetchone()[0]

        return f"""
        <html>
        <body>

            <h1>DOCUMENT_CHUNKS Accessible</h1>

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

            <h1>DOCUMENT_CHUNKS Test Failed</h1>

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