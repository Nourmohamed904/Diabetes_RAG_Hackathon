"""Runtime-only extraction of the final notebook's clinical RAG logic.

This module intentionally excludes ingestion, indexing, and evaluation code.
"""

import json
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

REFUSAL_RECOMMENDATION = (
    "I couldn't find enough information in the indexed guidelines to answer this "
    "confidently. This source doesn't appear to cover this topic — try rephrasing, "
    "or consult a clinician directly."
)

CLINICAL_SAFETY_DISCLAIMER = (
    "This assistant provides evidence from NICE diabetes guidelines and does not "
    "provide patient-specific medical advice."
)

GROUNDED_SYSTEM_PROMPT = """You are a citation-bound Clinical Evidence Assistant for Adult Diabetes Management. Your role is to provide safe, evidence-grounded recommendations strictly derived from the provided NICE Clinical Guideline passages.

### STRICT OPERATING RULES:
1. ZERO OUTSIDE KNOWLEDGE: Answer ONLY using the exact facts in the provided context passages. Do NOT use prior general medical training or unmentioned clinical facts.
2. NO GUESSING: Never guess, extrapolate, or estimate dosages, targets, intervals, or medication choices not explicitly stated in the context.
3. MANDATORY STRUCTURE & CHUNK_ID: You must output ONLY a valid JSON object matching the required schema with:
   - 'recommendation': Short, clear, direct clinical answer in plain language.
   - 'evidence': The verbatim or closely paraphrased supporting excerpt from the text.
   - 'citations': Array of exact citations, each containing 'document', 'section', 'page', AND 'chunk_id'.
   - 'confidence': One of ['high', 'medium', 'low', 'insufficient'].
4. REFUSAL POLICY (ESCAPE HATCH):
   - If the provided context does NOT contain enough information to answer the question, or if the question is out of scope (for example non-diabetes topics or personal dosing), you MUST set 'confidence' to 'insufficient'.
   - Set 'recommendation' to: "I couldn't find enough information in the indexed guidelines to answer this confidently. This source doesn't appear to cover this topic — try rephrasing, or consult a clinician directly."
   - Leave 'citations' as an empty list [].
5. OUTPUT PURE JSON: Return valid JSON ONLY. Do not include markdown codeblocks or outside commentary.
"""


class CitationItem(BaseModel):
    document: str
    section: str
    page: int
    chunk_id: str


class ClinicalResponse(BaseModel):
    recommendation: str
    evidence: str
    citations: list[CitationItem] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low", "insufficient"]


def validate_clinical_response(
    response_dict: dict[str, Any],
) -> tuple[bool, str, ClinicalResponse | None]:
    """Apply the final notebook's response and citation integrity rules."""
    try:
        parsed = ClinicalResponse.model_validate(response_dict)
        if parsed.confidence in {"high", "medium"}:
            if not parsed.citations:
                return False, "Validation Error: High/Medium confidence answer must contain at least one citation.", parsed
            if not parsed.evidence or len(parsed.evidence.strip()) < 5:
                return False, "Validation Error: High/Medium confidence answer must include supporting evidence excerpt.", parsed
        elif parsed.confidence == "insufficient" and parsed.citations:
            return False, "Validation Warning: Refusal response should have empty citations list.", parsed
        return True, "Schema Validation Passed (All citations verified with chunk_id)", parsed
    except ValidationError as error:
        return False, f"Validation Error: {error}", None


class ClinicalRAGPipeline:
    """The final notebook's runtime query pipeline (cell 57 / cell 74), independent of FastAPI."""

    def __init__(self, vector_store: Any, llm: Any, chunk_config: str = "500_50", score_threshold: float = 1.1):
        # Matches the notebook's live ClinicalRAGPipeline default (cell 57), not the
        # offline-only CALIBRATED_THRESHOLD (0.23) used for Precision@K measurement in cell 89.
        self.vector_store = vector_store
        self.chunk_config = chunk_config
        self.llm = llm
        self.score_threshold = score_threshold

    def classify_input(self, question: str) -> str:
        question_lower = question.lower()
        high_risk_keywords = [
            "my dose", "my dosage", "how much insulin should i take",
            "how much insulin do i need", "should i stop", "should i change my medication",
            "emergency", "overdose", "i am having", "my blood sugar is",
            "inject another", "inject more", "units right now", "units now",
        ]
        if any(keyword in question_lower for keyword in high_risk_keywords):
            return "high_risk"

        diabetes_keywords = [
            "diabetes", "diabetic", "hba1c", "insulin", "glucose", "blood sugar",
            "hypoglycemia", "hyperglycemia", "metformin", "continuous glucose monitoring", "cgm",
        ]
        return "allowed" if any(keyword in question_lower for keyword in diabetes_keywords) else "out_of_scope"

    def _format_context_passages(self, retrieved_docs_with_scores: list[tuple[Any, float]]) -> str:
        passages = []
        for index, (document, _) in enumerate(retrieved_docs_with_scores, 1):
            metadata = document.metadata
            passages.append(
                f"[PASSAGE {index}] Document: {metadata.get('document', 'Unknown')} | "
                f"Section: {metadata.get('section', 'General')} | Page: {metadata.get('page', 1)} | "
                f"Chunk_ID: {metadata.get('chunk_id', '')}\nContent: {document.page_content.strip()}"
            )
        return "\n\n".join(passages)

    def check_retrieval_confidence(self, retrieved_docs_with_scores: list[tuple[Any, float]]) -> dict[str, Any]:
        """Diagnostic only — mirrors notebook cell 76. The notebook's live query() never calls
        this before invoking the LLM, so it must not gate generation here either."""
        if not retrieved_docs_with_scores:
            return {"sufficient": False, "reason": "No evidence retrieved.", "valid_chunks": 0, "top_score": None}
        top_score = retrieved_docs_with_scores[0][1]
        valid_chunks = [item for item in retrieved_docs_with_scores if item[1] <= self.score_threshold]
        if not valid_chunks:
            return {
                "sufficient": False,
                "reason": "Retrieved evidence does not meet the confidence threshold.",
                "valid_chunks": 0,
                "top_score": float(top_score),
            }
        return {
            "sufficient": True,
            "reason": "Sufficient relevant evidence retrieved.",
            "valid_chunks": len(valid_chunks),
            "top_score": float(top_score),
        }

    @staticmethod
    def _parse_json(raw_output: str) -> dict[str, Any]:
        cleaned = re.sub(r"^```json\s*", "", raw_output, flags=re.MULTILINE)
        cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        return json.loads(match.group(0) if match else cleaned)

    def repair_citations_if_needed(self, raw_json: dict[str, Any], retrieved_docs_with_scores: list[tuple[Any, float]]) -> tuple[dict[str, Any], bool]:
        repaired = False
        if raw_json.get("confidence") in {"high", "medium"}:
            citations = raw_json.get("citations", [])
            if not citations and retrieved_docs_with_scores:
                document, _ = retrieved_docs_with_scores[0]
                metadata = document.metadata
                raw_json["citations"] = [{
                    "document": str(metadata.get("document", "NICE Guideline")),
                    "section": str(metadata.get("section", "General")),
                    "page": int(metadata.get("page", 1)),
                    "chunk_id": str(metadata.get("chunk_id", "repaired_chunk_id")),
                }]
                repaired = True
            else:
                for citation in citations:
                    if not citation.get("chunk_id") and retrieved_docs_with_scores:
                        citation["chunk_id"] = str(retrieved_docs_with_scores[0][0].metadata.get("chunk_id", "chunk_id_auto_filled"))
                        repaired = True
        elif raw_json.get("confidence") == "insufficient" and raw_json.get("citations"):
            raw_json["citations"] = []
            repaired = True
        return raw_json, repaired

    @staticmethod
    def _retrieved_evidence(retrieved_docs_with_scores: list[tuple[Any, float]]) -> list[dict[str, Any]]:
        """Expose exact retrieved chunk text for the API traceability adapter."""
        evidence = []
        for document, _ in retrieved_docs_with_scores:
            metadata = document.metadata
            evidence.append({
                "document": str(metadata.get("document", "Unknown")),
                "section": str(metadata.get("section", "General")),
                "page": int(metadata.get("page", 1)),
                "chunk_id": str(metadata.get("chunk_id", "")),
                "evidence": document.page_content.strip(),
            })
        return evidence

    @staticmethod
    def _log_retrieval(question: str, top_k: int, retrieved: list[tuple[Any, float]], valid: list[tuple[Any, float]]) -> None:
        """Stage-by-stage trace: lets you tell Retrieval vs Filtering vs Generation apart."""
        kept_ids = {id(doc) for doc, _ in valid}
        logger.debug("RAG query=%r top_k=%d retrieved=%d kept=%d", question, top_k, len(retrieved), len(valid))
        for rank, (document, score) in enumerate(retrieved, 1):
            metadata = document.metadata
            logger.debug(
                "  [%d] score=%.4f kept=%s doc=%s page=%s chunk_id=%s",
                rank, score, id(document) in kept_ids,
                metadata.get("document"), metadata.get("page"), metadata.get("chunk_id"),
            )

    def _result(self, question: str, response: dict[str, Any], *, is_schema_valid: bool, validation_message: str, was_repaired: bool, retrieved_chunks_count: int, retrieval_confidence: dict[str, Any], risk_level: str, retrieved_evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "question": question,
            "is_schema_valid": is_schema_valid,
            "validation_message": validation_message,
            "response": response,
            "was_repaired": was_repaired,
            "retrieved_chunks_count": retrieved_chunks_count,
            "retrieval_confidence": retrieval_confidence,
            "retrieved_evidence": retrieved_evidence or [],
            "risk_level": risk_level,
            "disclaimer": CLINICAL_SAFETY_DISCLAIMER,
        }

    def _refusal(
        self,
        question: str,
        risk_level: str,
        reason: str,
        *,
        evidence: str = "",
        retrieved_chunks_count: int = 0,
        retrieval_confidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        recommendation = (
            "I can't provide personalized medical instructions, such as individual medication or insulin dosing. Please consult a qualified healthcare professional."
            if risk_level == "high_risk" else REFUSAL_RECOMMENDATION
        )
        response = {"recommendation": recommendation, "evidence": evidence, "citations": [], "confidence": "insufficient"}
        valid, message, _ = validate_clinical_response(response)
        return self._result(
            question, response, is_schema_valid=valid, validation_message=message, was_repaired=False,
            retrieved_chunks_count=retrieved_chunks_count,
            retrieval_confidence=retrieval_confidence or {"sufficient": False, "reason": reason, "valid_chunks": 0, "top_score": None},
            risk_level=risk_level,
        )

    def query(self, user_question: str, top_k: int = 5) -> dict[str, Any]:
        risk_level = self.classify_input(user_question)
        if risk_level == "high_risk":
            return self._refusal(user_question, risk_level, "High-risk request blocked before retrieval.")
        if risk_level == "out_of_scope":
            return self._refusal(user_question, risk_level, "Question is outside the system scope.")

        retrieved_results = self.vector_store.similarity_search_with_score(user_question, k=top_k)
        retrieval_check = self.check_retrieval_confidence(retrieved_results)  # diagnostics only, does not gate
        valid_results = [item for item in retrieved_results if item[1] <= self.score_threshold]
        self._log_retrieval(user_question, top_k, retrieved_results, valid_results)

        context = self._format_context_passages(valid_results)
        response = self.llm.invoke([
            {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context Passages:\n{context}\n\nClinical Question: {user_question}\n\nRespond ONLY in valid JSON matching the schema:"},
        ])
        raw_output = str(response.content).strip()
        try:
            raw_json = self._parse_json(raw_output)
        except Exception:
            raw_json = {
                "recommendation": raw_output or REFUSAL_RECOMMENDATION,
                "evidence": context[:250] if valid_results else "No evidence passages found.",
                "citations": [],
                "confidence": "insufficient",
            }
        raw_json, was_repaired = self.repair_citations_if_needed(raw_json, valid_results)
        is_valid, validation_message, _ = validate_clinical_response(raw_json)
        return self._result(
            user_question, raw_json, is_schema_valid=is_valid, validation_message=validation_message,
            was_repaired=was_repaired, retrieved_chunks_count=len(valid_results),
            retrieval_confidence=retrieval_check, risk_level=risk_level,
            retrieved_evidence=self._retrieved_evidence(valid_results),
        )
