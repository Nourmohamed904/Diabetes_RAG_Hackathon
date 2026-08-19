"""Stable HTTP contract between the React client and the RAG pipeline."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """A question submitted to the clinical evidence assistant."""

    question: str = Field(min_length=1, max_length=2_000)


class Citation(BaseModel):
    """Traceable source metadata for a supported claim."""

    model_config = ConfigDict(populate_by_name=True)

    document: str
    section: str
    page: int = Field(ge=1)
    chunk_id: str = Field(alias="chunkId")
    evidence: str


class Claim(BaseModel):
    text: str
    citations: list[Citation]


class QueryResponse(BaseModel):
    """The UI-facing result of a clinical RAG query.

    `status` distinguishes a successful evidence response from deliberate
    abstentions/safety boundaries. Server failures use HTTP error responses.
    """

    status: Literal["supported", "insufficient", "safety"]
    question: str
    recommendation: str
    confidence: Literal["high", "medium", "low", "insufficient", "not-assessed"]
    claims: list[Claim]
