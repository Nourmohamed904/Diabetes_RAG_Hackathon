import os
import re
import json

from typing import List, Literal, Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


# ============================================================
# 1. ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# 2. CONFIGURATION
# ============================================================

CHROMA_DIR = "./chroma_500_50"

COLLECTION_NAME = "diabetes_500_50"

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

GROQ_MODEL = "openai/gpt-oss-120b"

TOP_K = 5

SCORE_THRESHOLD = 1.1


# ============================================================
# 3. GROUNDED SYSTEM PROMPT
# ============================================================

GROUNDED_SYSTEM_PROMPT = """
You are a citation-bound Clinical Evidence Assistant for Adult Diabetes Management.

Your role is to provide safe, evidence-grounded recommendations strictly derived
from the provided NICE Clinical Guideline passages.

STRICT OPERATING RULES:

1. ZERO OUTSIDE KNOWLEDGE:
Answer ONLY using the exact facts in the provided context passages.
Do NOT use prior general medical training or unmentioned clinical facts.

2. NO GUESSING:
Never guess, extrapolate, or estimate dosages, targets, intervals,
or medication choices not explicitly stated in the context.

3. REQUIRED JSON STRUCTURE:

Return ONLY a valid JSON object containing:

{
  "recommendation": "...",
  "evidence": "...",
  "citations": [
    {
      "document": "...",
      "section": "...",
      "page": 0,
      "chunk_id": "..."
    }
  ],
  "confidence": "high"
}

4. CONFIDENCE:

Use one of:

- high
- medium
- low
- insufficient

5. REFUSAL POLICY:

If the provided context does NOT contain enough information to answer
the question, or if the question is outside the scope of adult diabetes
management, set confidence to "insufficient".

For insufficient answers use exactly:

"I couldn't find enough information in the indexed guidelines to answer
this confidently. This source doesn't appear to cover this topic —
try rephrasing, or consult a clinician directly."

For insufficient answers:

"citations": []

6. CITATIONS:

For high or medium confidence answers, every citation MUST contain:

- document
- section
- page
- chunk_id

7. OUTPUT PURE JSON:

Return valid JSON ONLY.

Do not use markdown code blocks.
Do not include explanations outside the JSON.
"""


# ============================================================
# 4. PYDANTIC SCHEMA
# ============================================================

class CitationItem(BaseModel):

    document: str = Field(
        description="Full name of guideline PDF"
    )

    section: str = Field(
        description="Exact guideline section"
    )

    page: int = Field(
        description="Page number"
    )

    chunk_id: str = Field(
        description="Unique chunk identifier"
    )


class ClinicalResponse(BaseModel):

    recommendation: str = Field(
        description="Direct clinical answer or refusal"
    )

    evidence: str = Field(
        description="Supporting guideline evidence"
    )

    citations: List[CitationItem] = Field(
        default_factory=list
    )

    confidence: Literal[
        "high",
        "medium",
        "low",
        "insufficient"
    ]


# ============================================================
# 5. RESPONSE VALIDATION
# ============================================================

def validate_clinical_response(
    response_dict: Dict[str, Any]
):

    try:

        parsed = ClinicalResponse(**response_dict)

        # High / Medium
        if parsed.confidence in ["high", "medium"]:

            if not parsed.citations:

                return (
                    False,
                    "High/Medium confidence requires citations.",
                    parsed
                )

            if (
                not parsed.evidence
                or len(parsed.evidence.strip()) < 5
            ):

                return (
                    False,
                    "High/Medium confidence requires evidence.",
                    parsed
                )

            for citation in parsed.citations:

                if (
                    not citation.document
                    or not citation.section
                    or citation.page <= 0
                    or not citation.chunk_id.strip()
                ):

                    return (
                        False,
                        "Incomplete citation metadata.",
                        parsed
                    )

        # Insufficient
        elif parsed.confidence == "insufficient":

            if parsed.citations:

                return (
                    False,
                    "Insufficient response must have empty citations.",
                    parsed
                )

        return (
            True,
            "Schema validation passed.",
            parsed
        )

    except ValidationError as e:

        return (
            False,
            f"Pydantic validation error: {e}",
            None
        )

    except Exception as e:

        return (
            False,
            f"Unexpected validation error: {e}",
            None
        )


# ============================================================
# 6. LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = FastEmbedEmbeddings(
    model_name=EMBEDDING_MODEL
)

print("Embedding model loaded.")


# ============================================================
# 7. LOAD CHROMA
# ============================================================

print("Loading Chroma vector store...")

vector_store = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embedding_model,
    collection_name=COLLECTION_NAME
)

vector_count = vector_store._collection.count()

print(
    f"Chroma loaded successfully. "
    f"Vectors: {vector_count}"
)


# ============================================================
# 8. INITIALIZE GROQ
# ============================================================

llm_engine = ChatGroq(
    model=GROQ_MODEL,
    temperature=0.0,
    groq_api_key=GROQ_API_KEY
)

print(
    f"Groq LLM initialized: {GROQ_MODEL}"
)


# ============================================================
# 9. CLINICAL RAG PIPELINE
# ============================================================

class ClinicalRAGPipeline:

    def __init__(
        self,
        vector_store,
        llm,
        chunk_config="500_50",
        score_threshold=1.1
    ):

        self.vector_store = vector_store

        self.llm = llm

        self.chunk_config = chunk_config

        self.score_threshold = score_threshold


    # --------------------------------------------------------
    # Format retrieved passages
    # --------------------------------------------------------

    def _format_context_passages(
        self,
        retrieved_docs_with_scores
    ):

        passages = []

        for idx, (doc, score) in enumerate(
            retrieved_docs_with_scores,
            1
        ):

            header = (
                f"[PASSAGE {idx}] "
                f"Document: "
                f"{doc.metadata.get('document', 'Unknown')} | "
                f"Section: "
                f"{doc.metadata.get('section', 'General')} | "
                f"Page: "
                f"{doc.metadata.get('page', 1)} | "
                f"Chunk_ID: "
                f"{doc.metadata.get('chunk_id', '')}"
            )

            passages.append(
                f"{header}\n"
                f"Content: {doc.page_content.strip()}"
            )

        return "\n\n".join(passages)


    # --------------------------------------------------------
    # Repair citations
    # --------------------------------------------------------

    def repair_citations_if_needed(
        self,
        raw_json,
        retrieved_docs_with_scores
    ):

        repaired = False

        confidence = raw_json.get("confidence")

        # High / Medium
        if confidence in ["high", "medium"]:

            citations = raw_json.get(
                "citations",
                []
            )

            # Missing citations
            if (
                not citations
                and retrieved_docs_with_scores
            ):

                top_doc, _ = (
                    retrieved_docs_with_scores[0]
                )

                raw_json["citations"] = [
                    {
                        "document": str(
                            top_doc.metadata.get(
                                "document",
                                "NICE Guideline"
                            )
                        ),

                        "section": str(
                            top_doc.metadata.get(
                                "section",
                                "General"
                            )
                        ),

                        "page": int(
                            top_doc.metadata.get(
                                "page",
                                1
                            )
                        ),

                        "chunk_id": str(
                            top_doc.metadata.get(
                                "chunk_id",
                                ""
                            )
                        )
                    }
                ]

                repaired = True

            # Missing chunk_id
            else:

                for citation in citations:

                    if (
                        not citation.get("chunk_id")
                        and retrieved_docs_with_scores
                    ):

                        citation["chunk_id"] = str(
                            retrieved_docs_with_scores[0][0]
                            .metadata.get(
                                "chunk_id",
                                ""
                            )
                        )

                        repaired = True

        # Insufficient
        elif confidence == "insufficient":

            if raw_json.get("citations"):

                raw_json["citations"] = []

                repaired = True

        return raw_json, repaired


    # --------------------------------------------------------
    # Main query
    # --------------------------------------------------------

    def query(
        self,
        user_question: str,
        top_k=TOP_K
    ):

        # 1. Retrieval
        retrieved_results = (
            self.vector_store
            .similarity_search_with_score(
                user_question,
                k=top_k
            )
        )

        # 2. Threshold
        valid_results = [
            (doc, score)
            for doc, score in retrieved_results
            if score <= self.score_threshold
        ]

        # 3. Context
        context_str = (
            self._format_context_passages(
                valid_results
            )
        )

        # 4. Prompt
        user_prompt = (
            f"Context Passages:\n"
            f"{context_str}\n\n"
            f"Clinical Question:\n"
            f"{user_question}\n\n"
            f"Respond ONLY in valid JSON."
        )

        messages = [

            {
                "role": "system",
                "content": GROUNDED_SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": user_prompt
            }

        ]

        # 5. LLM
        response = self.llm.invoke(messages)

        raw_output = str(
            response.content
        ).strip()

        # 6. Clean JSON
        cleaned = re.sub(
            r"^```json\s*",
            "",
            raw_output,
            flags=re.MULTILINE
        )

        cleaned = re.sub(
            r"^```\s*",
            "",
            cleaned,
            flags=re.MULTILINE
        ).strip()

        # 7. Parse JSON
        try:

            json_match = re.search(
                r"\{.*\}",
                cleaned,
                re.DOTALL
            )

            if json_match:

                raw_json = json.loads(
                    json_match.group(0)
                )

            else:

                raw_json = json.loads(cleaned)

        except Exception:

            raw_json = {

                "recommendation": (
                    "I couldn't find enough information "
                    "in the indexed guidelines to answer "
                    "this confidently."
                ),

                "evidence": "",

                "citations": [],

                "confidence": "insufficient"
            }

        # 8. Repair
        raw_json, was_repaired = (
            self.repair_citations_if_needed(
                raw_json,
                valid_results
            )
        )

        # 9. Validate
        (
            is_valid,
            validation_message,
            parsed_model
        ) = validate_clinical_response(
            raw_json
        )

        # 10. Return
        return {

            "question": user_question,

            "answer": raw_json.get(
                "recommendation",
                ""
            ),

            "evidence": raw_json.get(
                "evidence",
                ""
            ),

            "citations": raw_json.get(
                "citations",
                []
            ),

            "confidence": raw_json.get(
                "confidence",
                "insufficient"
            ),

            "is_schema_valid": is_valid,

            "validation_message": validation_message,

            "was_repaired": was_repaired,

            "retrieved_chunks_count": len(
                valid_results
            )
        }


# ============================================================
# 10. CREATE PIPELINE INSTANCE
# ============================================================

pipeline = ClinicalRAGPipeline(
    vector_store=vector_store,
    llm=llm_engine,
    chunk_config="500_50",
    score_threshold=SCORE_THRESHOLD
)

print("Clinical RAG Pipeline initialized successfully.")


# ============================================================
# 11. SIMPLE FUNCTION FOR THE API
# ============================================================

def ask_clinical_question(
    question: str
):

    result = pipeline.query(question)

    return {

        "answer": result["answer"],

        "confidence": result["confidence"],

        "citations": result["citations"],

        "evidence": result["evidence"],

        "is_schema_valid": result["is_schema_valid"]
    }