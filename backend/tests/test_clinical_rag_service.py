"""Unit tests for the API adapter; no vector index or external model is needed."""

import unittest

from app.services.clinical_rag_service import ClinicalRAGService


class FakePipeline:
    def __init__(self, result):
        self.result = result

    def query(self, _question):
        return self.result


class ClinicalRAGServiceTests(unittest.TestCase):
    question = "What HbA1c target should adults with type 1 diabetes aim for?"

    def test_supported_response_uses_exact_retrieved_chunk_text(self):
        result = {
            "risk_level": "allowed", "is_schema_valid": True,
            "response": {
                "recommendation": "Aim for the stated target.", "confidence": "high",
                "citations": [{"document": "Type-1 diabetes.pdf", "section": "1.6", "page": 18, "chunk_id": "chunk-1"}],
            },
            "retrieved_evidence": [{
                "document": "Type-1 diabetes.pdf", "section": "1.6", "page": 18,
                "chunk_id": "chunk-1", "evidence": "Exact retrieved guideline text.",
            }],
        }
        response = ClinicalRAGService(FakePipeline(result)).query(self.question)
        self.assertEqual(response.status, "supported")
        self.assertEqual(response.claims[0].citations[0].evidence, "Exact retrieved guideline text.")
        self.assertEqual(response.claims[0].citations[0].chunk_id, "chunk-1")

    def test_high_risk_result_maps_to_safety_not_insufficient(self):
        result = {"risk_level": "high_risk", "response": {"recommendation": "Do not dose yourself.", "confidence": "insufficient"}}
        response = ClinicalRAGService(FakePipeline(result)).query(self.question)
        self.assertEqual(response.status, "safety")
        self.assertEqual(response.confidence, "not-assessed")

    def test_untraceable_citation_becomes_insufficient(self):
        result = {
            "risk_level": "allowed", "is_schema_valid": True,
            "response": {"recommendation": "Claim", "confidence": "high", "citations": [{"chunk_id": "unknown"}]},
            "retrieved_evidence": [],
        }
        response = ClinicalRAGService(FakePipeline(result)).query(self.question)
        self.assertEqual(response.status, "insufficient")
        self.assertEqual(response.claims, [])
