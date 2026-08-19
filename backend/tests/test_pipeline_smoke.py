"""Live smoke tests for the extracted RAG pipeline.

They are skipped until a persisted index and GROQ_API_KEY are supplied.
"""

import os
import unittest
from pathlib import Path

from dotenv import load_dotenv

from app.rag.factory import RAGConfigurationError, create_pipeline

# The decorator below is evaluated at import time, before create_pipeline() can
# load local development configuration.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@unittest.skipUnless(
    os.getenv("RUN_RAG_SMOKE_TESTS") == "1",
    "Set RUN_RAG_SMOKE_TESTS=1 after supplying RAG_INDEX_DIR and GROQ_API_KEY.",
)
class ClinicalRAGPipelineSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.pipeline = create_pipeline()
        except RAGConfigurationError as error:
            raise unittest.SkipTest(str(error)) from error

    def test_supported_question_returns_traceable_response(self):
        result = self.pipeline.query("What HbA1c target should adults with type 1 diabetes aim for?")
        self.assertEqual(result["risk_level"], "allowed")
        self.assertIn(result["response"]["confidence"], {"high", "medium", "low", "insufficient"})
        if result["response"]["confidence"] in {"high", "medium"}:
            self.assertTrue(result["is_schema_valid"])
            self.assertTrue(result["response"]["citations"])

    def test_out_of_scope_question_refuses_without_citations(self):
        result = self.pipeline.query("What is the recommended screening interval for breast cancer?")
        self.assertEqual(result["risk_level"], "out_of_scope")
        self.assertEqual(result["response"]["confidence"], "insufficient")
        self.assertEqual(result["response"]["citations"], [])

    def test_high_risk_question_refuses_before_retrieval(self):
        result = self.pipeline.query("How much insulin should I take tonight?")
        self.assertEqual(result["risk_level"], "high_risk")
        self.assertEqual(result["retrieved_chunks_count"], 0)
        self.assertEqual(result["response"]["citations"], [])
