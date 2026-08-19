"""Temporary RAG implementation used to validate the web integration.

Replace this service's `query` implementation in Phase 3; keep the
`QueryResponse` return type so the API and UI do not need to change.
"""

from app.schemas.query import Citation, Claim, QueryResponse


class MockRAGService:
    def query(self, question: str) -> QueryResponse:
        normalized = question.strip().lower()

        if "inject another" in normalized or "dose" in normalized or "units right now" in normalized:
            return QueryResponse(
                status="safety",
                question=question,
                recommendation=(
                    "This request needs an immediate, patient-specific clinical assessment. "
                    "The Evidence Assistant does not provide individual dosing instructions."
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

        if "insulin regimen" in normalized:
            return self._insulin_response(question)
        if "sglt" in normalized:
            return self._sglt_response(question)
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

    @staticmethod
    def _insulin_response(question: str) -> QueryResponse:
        recommendation = "Multiple daily injection basal–bolus insulin regimens are the recommended default approach for adults with type 1 diabetes."
        return QueryResponse(
            status="supported", question=question, recommendation=recommendation, confidence="medium",
            claims=[Claim(text="Offer multiple daily injection basal–bolus insulin regimens as the insulin injection regimen for adults with type 1 diabetes.", citations=[Citation(
                document="NICE NG17 · Type 1 diabetes in adults", section="1.7 Insulin therapy", page=21,
                chunk_id="300_60_chunk_00146", evidence="Offer multiple daily injection basal–bolus insulin regimens, rather than twice-daily mixed insulin regimens, as the insulin injection regimen for adults with type 1 diabetes.",
            )])],
        )

    @staticmethod
    def _sglt_response(question: str) -> QueryResponse:
        recommendation = "Before starting an SGLT-2 inhibitor, assess suitability and discuss risks as described in the relevant NICE type 2 diabetes guidance."
        return QueryResponse(
            status="supported", question=question, recommendation=recommendation, confidence="medium",
            claims=[Claim(text="Suitability and risks should be assessed before initiating an SGLT-2 inhibitor in adults with type 2 diabetes.", citations=[Citation(
                document="NICE NG28 · Type 2 diabetes in adults", section="1.7 Blood glucose management", page=26,
                chunk_id="300_60_chunk_00218", evidence="When starting treatment with an SGLT2 inhibitor, discuss the benefits and risks with the person, taking into account their clinical circumstances and preferences.",
            )])],
        )
