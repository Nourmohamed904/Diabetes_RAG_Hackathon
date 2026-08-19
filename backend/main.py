from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rag_pipeline import ask_clinical_question


# ============================================================
# FastAPI APP
# ============================================================

app = FastAPI(
    title="Diabetes Clinical RAG API",
    description="NICE-guideline grounded diabetes assistant",
    version="1.0.0"
)


# ============================================================
# REQUEST MODEL
# ============================================================

class QuestionRequest(BaseModel):
    question: str


# ============================================================
# RESPONSE MODEL
# ============================================================

class QuestionResponse(BaseModel):
    answer: str
    confidence: str
    citations: list
    evidence: str
    is_schema_valid: bool


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Diabetes Clinical RAG API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# ASK ENDPOINT
# ============================================================

@app.post(
    "/ask",
    response_model=QuestionResponse
)
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = ask_clinical_question(question)

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )