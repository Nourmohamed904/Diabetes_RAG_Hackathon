from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Load the same embedding model used to build the Chroma index
embedding_model = FastEmbedEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)

# Load the persisted Chroma database
db = Chroma(
    persist_directory="./chroma_500_50",
    embedding_function=embedding_model,
    collection_name="diabetes_500_50"
)

print("Chroma loaded successfully!")
print("Number of vectors:", db._collection.count())

query = "What HbA1c target should adults with type 1 diabetes generally aim for?"

results = db.similarity_search_with_score(query, k=5)

print("\nTop retrieved chunks:")
for i, (doc, score) in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print("Score:", score)
    print("Document:", doc.metadata.get("document"))
    print("Section:", doc.metadata.get("section"))
    print("Page:", doc.metadata.get("page"))
    print("Chunk ID:", doc.metadata.get("chunk_id"))
    print("Content:", doc.page_content[:300])