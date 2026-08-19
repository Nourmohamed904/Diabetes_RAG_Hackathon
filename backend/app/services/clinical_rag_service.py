"""Adapter from the final RAG pipeline result to the stable API/UI contract."""

from typing import Any

from app.rag.pipeline import REFUSAL_RECOMMENDATION
from app.schemas.query import Citation, Claim, QueryResponse


class ClinicalRAGServiceError(RuntimeError):
    """A technical failure that must be reported separately from a clinical refusal."""


class ClinicalRAGService:
    def __init__(self, pipeline: Any):
        self.pipeline = pipeline

    def query(self, question: str) -> QueryResponse:
        try:
            result = self.pipeline.query(question)
        except Exception as error:
            raise ClinicalRAGServiceError("Clinical RAG pipeline execution failed.") from error

        risk_level = result.get("risk_level")
        response = result.get("response", {})
        confidence = response.get("confidence", "insufficient")

        if risk_level == "high_risk":
            return QueryResponse(
                status="safety", question=question,
                recommendation=response.get("recommendation", REFUSAL_RECOMMENDATION),
                confidence="not-assessed", claims=[],
            )
        if confidence == "insufficient":
            return self._insufficient(question, response.get("recommendation", REFUSAL_RECOMMENDATION))
        if not result.get("is_schema_valid"):
            return self._insufficient(question, REFUSAL_RECOMMENDATION)

        citations = self._traceable_citations(response.get("citations", []), result.get("retrieved_evidence", []))
        if not citations:
            # A non-refusal answer without verifiable retrieved evidence is unsafe to present.
            return self._insufficient(question, REFUSAL_RECOMMENDATION)

        recommendation = response.get("recommendation", "").strip()
        if not recommendation:
            raise ClinicalRAGServiceError("Clinical RAG pipeline returned an empty recommendation.")
        return QueryResponse(
            status="supported",
            question=question,
            recommendation=recommendation,
            confidence=confidence,
            claims=[Claim(text=recommendation, citations=citations)],
        )

    @staticmethod
    def _insufficient(question: str, recommendation: str) -> QueryResponse:
        return QueryResponse(
            status="insufficient", question=question, recommendation=recommendation,
            confidence="insufficient", claims=[],
        )

    @staticmethod
    def _traceable_citations(raw_citations: list[dict[str, Any]], retrieved_evidence: list[dict[str, Any]]) -> list[Citation]:
        evidence_by_chunk_id = {
            item.get("chunk_id"): item
            for item in retrieved_evidence
            if item.get("chunk_id") and item.get("evidence")
        }
        citations = []
        for raw_citation in raw_citations:
            exact_chunk = evidence_by_chunk_id.get(raw_citation.get("chunk_id"))
            if not exact_chunk:
                # Do not pass through an LLM citation that cannot be traced to a retrieved chunk.
                continue
            citations.append(Citation(
                document=str(raw_citation.get("document", exact_chunk["document"])),
                section=str(raw_citation.get("section", exact_chunk["section"])),
                page=int(raw_citation.get("page", exact_chunk["page"])),
                chunk_id=str(raw_citation["chunk_id"]),
                evidence=str(exact_chunk["evidence"]),
            ))
        return citations
