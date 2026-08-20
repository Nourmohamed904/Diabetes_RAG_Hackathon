"""One-time construction of the real RAG pipeline from deployment configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

from app.rag.pipeline import ClinicalRAGPipeline


class RAGConfigurationError(RuntimeError):
    """Raised when required RAG assets or configuration are unavailable."""


def _required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RAGConfigurationError(f"{name} is required to initialize the clinical RAG pipeline.")
    return value


def create_pipeline() -> ClinicalRAGPipeline:
    """Load the embedding model, persisted final index, and Groq client once."""
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_groq import ChatGroq

    backend_root = Path(__file__).resolve().parents[2]
    # Deployment environment variables take precedence; .env is local-development convenience.
    load_dotenv(backend_root / ".env")
    index_directory = Path(os.getenv("RAG_INDEX_DIR", backend_root / "rag_data" / "chroma_500_50"))
    cache_directory = Path(os.getenv("FASTEMBED_CACHE_DIR", backend_root / "rag_data" / "fastembed_cache"))
    if not index_directory.is_dir():
        raise RAGConfigurationError(
            f"Persisted Chroma index is missing: {index_directory}. "
            "Provide chroma_500_50 before starting the API; it will not be rebuilt automatically."
        )

    cache_directory.mkdir(parents=True, exist_ok=True)
    embedding_model = FastEmbedEmbeddings(
        model_name=os.getenv("FASTEMBED_MODEL", "BAAI/bge-base-en-v1.5"),
        cache_dir=str(cache_directory),
    )
    vector_store = Chroma(
        persist_directory=str(index_directory),
        embedding_function=embedding_model,
        collection_name=os.getenv("CHROMA_COLLECTION", "diabetes_500_50"),
    )
    if vector_store._collection.count() == 0:
        raise RAGConfigurationError(f"Persisted Chroma index is empty: {index_directory}.")

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0.0,
        groq_api_key=_required_environment("GROQ_API_KEY"),
    )
    return ClinicalRAGPipeline(
        vector_store=vector_store,
        chunk_config="500_50",
        llm=llm,
        score_threshold=float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "1.1")),
    )
