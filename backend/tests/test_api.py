"""HTTP-level contract tests that do not initialize the real RAG dependencies."""

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.query import QueryResponse
from app.services.clinical_rag_service import ClinicalRAGServiceError


class FakeRAGService:
    def query(self, question: str) -> QueryResponse:
        return QueryResponse(
            status="supported", question=question, recommendation="Grounded answer.", confidence="high", claims=[],
        )


class FailingRAGService:
    def query(self, _question: str) -> QueryResponse:
        raise ClinicalRAGServiceError("Simulated technical failure.")


class EvidenceAPIContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.state.rag_service = FakeRAGService()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_query_returns_valid_api_contract(self):
        response = self.client.post("/query", json={"question": "What is the HbA1c target?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "supported")
        self.assertEqual(response.json()["question"], "What is the HbA1c target?")

    def test_empty_question_is_rejected(self):
        response = self.client.post("/query", json={"question": ""})
        self.assertEqual(response.status_code, 422)

    def test_technical_rag_failure_returns_503(self):
        app.state.rag_service = FailingRAGService()
        response = self.client.post("/query", json={"question": "What is the HbA1c target?"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Clinical evidence service is temporarily unavailable.")
