"""Temporary RAG implementation used to validate the web integration.

Replace this service's `query` implementation in Phase 3; keep the
`QueryResponse` return type so the API and UI do not need to change.
"""

from app.schemas.query import Citation, Claim, QueryResponse
from app.rag.pipeline import MEDICATION_SAFETY_KEYWORDS


class MockRAGService:
    def query(self, question: str) -> QueryResponse:
        normalized = question.strip().lower()

        if any(keyword in normalized for keyword in MEDICATION_SAFETY_KEYWORDS):
            return QueryResponse(
                status="safety",
                question=question,
                recommendation=(
                    "This assistant does not provide information or recommendations about medicines, "
                    "medication, insulin, or doses. Please consult a qualified healthcare professional."
                ),
                confidence="not-assessed",
                claims=[],
            )

        if "breast cancer" in normalized or "screening interval" in normalized:
            return QueryResponse(
                status="insufficient",
                question=question,
                recommendation=(
                    "I could not find enough information in the indexed NICE diabetes guidelines "
                    "to answer this confidently."
                ),
                confidence="insufficient",
                claims=[],
            )

        return self._hba1c_response(question)

    @staticmethod
    def _hba1c_response(question: str) -> QueryResponse:
        recommendation = "Adults with type 1 diabetes should generally aim for an HbA1c level of 48 mmol/mol (6.5%) or lower."
        return QueryResponse(
            status="supported",
            question=question,
            recommendation=recommendation,
            confidence="high",
            claims=[Claim(text=recommendation, citations=[Citation(
                document="NICE NG17 · Type 1 diabetes in adults",
                section="1.6 Blood glucose management",
                page=18,
                chunk_id="300_60_chunk_00125",
                evidence="Support adults with type 1 diabetes to aim for a target HbA1c level of 48 mmol/mol (6.5%) or lower, to minimise the risk of long-term vascular complications.",
            )])],
        )
