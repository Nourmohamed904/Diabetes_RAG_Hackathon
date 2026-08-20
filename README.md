# NICE Diabetes Evidence Assistant

[**Open the live demo → diabetes-rag-hackathon.vercel.app**](https://diabetes-rag-hackathon.vercel.app/)

An evidence-grounded clinical RAG demonstration for adult Type 1 and Type 2 diabetes. The system retrieves from the approved NICE guideline corpus, answers only when retrieved evidence supports the answer, provides traceable citations, and safely abstains when evidence is insufficient or a request is patient-specific.

The deployed React frontend runs on Vercel and calls the deployed FastAPI/RAG backend on Railway.

## Approved sources

- NICE NG17 — Type 1 diabetes in adults
- NICE NG28 — Type 2 diabetes in adults

This is a clinical decision-support demonstration, not a substitute for professional medical advice or a general medical chatbot.

## Architecture

```text
React frontend
  → POST /query
  → FastAPI backend
  → ClinicalRAGPipeline
  → Chroma vector search over indexed NICE chunks
  → retrieval diagnostics and grounded LLM assessment
  → Groq grounded generation
  → citation validation and exact-evidence traceability
  → React result view
```

The backend starts expensive resources once: the FastEmbed embedding model, the persisted Chroma index, the Groq client, and the RAG pipeline. They are not recreated for every user question.

## Deployment

- **Frontend:** [Vercel live demo](https://diabetes-rag-hackathon.vercel.app/)
- **Backend:** [Railway API health check](https://diabetesraghackathon-production.up.railway.app/health)

For the deployed frontend, the Vercel environment variable `VITE_API_URL` points to the Railway backend. For local development, it points to `http://localhost:8000`.

## Repository layout

```text
frontend/                    React + Vite user interface
backend/
  app/                       FastAPI API, RAG runtime, and services
  tests/                     API, adapter, safety, and smoke tests
  rag_data/                  Local-only generated RAG assets (not committed)
data/                        Source NICE PDFs
Diabetes_RAG_Hackathon_Submission_FINAL_Git_Data_(3).ipynb
                             Source-of-truth RAG notebook
```

## Prerequisites

- Python 3.13 or compatible installed locally
- Node.js and npm
- A Groq API key with access to the configured model
- The pre-built `chroma_500_50` Chroma folder exported from the final notebook

## Local setup

### 1. Configure RAG assets

Place the pre-built index here:

```text
backend/rag_data/chroma_500_50/
```

The first real run downloads and caches the FastEmbed model under:

```text
backend/rag_data/fastembed_cache/
```

These are generated assets and are intentionally excluded from Git.

### 2. Configure backend environment variables

```powershell
cd backend
Copy-Item .env.example .env
```

Edit `backend/.env` and set the real key locally:

```text
GROQ_API_KEY=your_real_key_here
```

Do not commit or share `.env`.

### 3. Install backend dependencies

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 4. Start the backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Backend URLs:

- API health: `http://127.0.0.1:8000/health`
- Interactive API docs: `http://127.0.0.1:8000/docs`

### 5. Start the frontend in a second terminal

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically `http://localhost:5173`. If port 5173 is already in use, Vite may use another local port; the backend development CORS configuration supports local `localhost` and `127.0.0.1` ports.

## API contract

### `GET /health`

```json
{
  "status": "healthy"
}
```

### `POST /query`

Request:

```json
{
  "question": "What HbA1c target should adults with Type 1 diabetes generally aim for?"
}
```

Supported response fields include a recommendation, confidence, claims, citation metadata, the source chunk ID, and exact retrieved evidence.

## Safety behavior

| Situation | API status | Result |
|---|---|---|
| Supported guideline question | `supported` | Grounded answer with traceable evidence |
| Insufficient or out-of-scope evidence | `insufficient` | Safe abstention with no citations |
| Patient-specific dosing / high-risk request | `safety` | Safety refusal with no retrieval or citations |
| Technical RAG failure | HTTP `503` | Frontend technical-error state |

The API never turns an intentional clinical refusal into a server error, and it does not display a citation unless it maps to an exact retrieved Chroma chunk.

## Tests

Run backend tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

The live smoke tests require `RUN_RAG_SMOKE_TESTS=1`, a valid `GROQ_API_KEY`, and the persisted Chroma index.

Build the frontend:

```powershell
cd frontend
npm run build
```

## Development notes

- The final notebook is the source of truth for RAG behavior. Do not modify it during backend runtime work.
- The backend uses the final production selection: `chroma_500_50` with a soft context-inclusion threshold of `1.1`. The earlier `0.23` value is retained only as an offline retrieval-evaluation reference; it must not reject live queries before the grounded model assesses the retrieved passages.
- The RAG flow has no separate pre-generation LLM sufficiency gate. Safety classification, grounded generation instructions, response-schema validation, and exact-citation traceability still protect the user-facing result.
- The Groq model and the FastEmbed model are configured in `backend/.env.example`.
- The repository keeps the final notebook and automated API, safety, adapter, and RAG smoke tests; older experimental notebooks were removed.
