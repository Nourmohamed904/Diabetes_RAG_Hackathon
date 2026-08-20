"""FastAPI entry point for the clinical evidence API."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas.query import QueryRequest, QueryResponse
from app.rag.factory import RAGConfigurationError, create_pipeline
from app.services.clinical_rag_service import ClinicalRAGService, ClinicalRAGServiceError

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

allowed_origins = {
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
}
if os.getenv("APP_ENV", "development") == "development":
    allowed_origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize the expensive embedding model, index, and LLM client once."""
    try:
        application.state.rag_service = ClinicalRAGService(create_pipeline())
        logger.info("Clinical RAG service initialized successfully.")
    except RAGConfigurationError:
        logger.exception("Clinical RAG service could not be initialized.")
        raise
    yield


app = FastAPI(title="NICE Diabetes Evidence API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_origin_regex=(r"^http://(localhost|127\.0\.0\.1):\d+$" if os.getenv("APP_ENV", "development") == "development" else None),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/version")
def version() -> dict[str, str]:
    """Reports the deployed commit so a stale Railway build can be diagnosed from the API itself."""
    return {
        "commit": os.getenv("RAILWAY_GIT_COMMIT_SHA", "unknown"),
        "branch": os.getenv("RAILWAY_GIT_BRANCH", "unknown"),
        "repo": os.getenv("RAILWAY_GIT_REPO_NAME", "unknown"),
    }


@app.post("/query", response_model=QueryResponse)
def query_evidence(request: QueryRequest, http_request: Request) -> QueryResponse:
    question = request.question.strip()
    logger.info("Clinical evidence query received (length=%d)", len(question))
    try:
        response = http_request.app.state.rag_service.query(question)
    except ClinicalRAGServiceError as error:
        logger.exception("Clinical RAG pipeline failed.")
        raise HTTPException(status_code=503, detail="Clinical evidence service is temporarily unavailable.") from error
    logger.info("Clinical evidence query completed (status=%s)", response.status)
    return response
