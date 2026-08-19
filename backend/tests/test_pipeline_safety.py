"""Offline checks for notebook safety paths that must not call Chroma or Groq."""

import unittest

from app.rag.pipeline import ClinicalRAGPipeline


class ClinicalRAGPipelineSafetyTests(unittest.TestCase):
    def setUp(self):
        # These paths return before retrieval or LLM generation, so dependencies are unnecessary.
        self.pipeline = ClinicalRAGPipeline(vector_store=None, llm=None)

    def test_high_risk_question_is_blocked_before_retrieval(self):
        result = self.pipeline.query("How much insulin should I take tonight?")
        self.assertEqual(result["risk_level"], "high_risk")
        self.assertEqual(result["retrieved_chunks_count"], 0)
        self.assertEqual(result["response"]["confidence"], "insufficient")
        self.assertEqual(result["response"]["citations"], [])

    def test_demo_insulin_injection_question_is_a_safety_refusal(self):
        result = self.pipeline.query("I am taking insulin. Should I inject another 8 units right now?")
        self.assertEqual(result["risk_level"], "high_risk")
        self.assertEqual(result["retrieved_chunks_count"], 0)
        self.assertEqual(result["response"]["citations"], [])

    def test_out_of_scope_question_is_refused_without_citations(self):
        result = self.pipeline.query("What is the recommended screening interval for breast cancer?")
        self.assertEqual(result["risk_level"], "out_of_scope")
        self.assertEqual(result["response"]["confidence"], "insufficient")
        self.assertEqual(result["response"]["citations"], [])
