from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"

model = TextEmbedding(model_name=MODEL_NAME)

question = "How can a Cloud Foundry application connect to SAP HANA Cloud?"

passages = [
    "Applications running on Cloud Foundry can consume credentials from bound service instances.",
    "SAP HANA Cloud provides database services for cloud applications.",
    "Users can customize the appearance of the SAP BTP cockpit."
]

query_vector = list(model.query_embed([question]))[0]
passage_vectors = list(model.passage_embed(passages))

print("Model:", MODEL_NAME)
print("Query vector dimension:", len(query_vector))
print("Number of passage vectors:", len(passage_vectors))
print("Passage vector dimension:", len(passage_vectors[0]))