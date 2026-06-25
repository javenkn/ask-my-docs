# Ask My Docs

A small web app for grounded question-answering: paste in some source text, ask a
question about it, and an LLM answers using **only** that text — and says "I don't
know" when the answer isn't there.

One screen, one feature, built to be correct and deployable rather than large.

A learning project exploring a full-stack LLM app end to end — a Next.js frontend, a
Python API backend, server-side LLM integration, and a containerized deploy.

```
┌──────────────┐      POST /ask           ┌──────────────┐     Messages API     ┌──────────┐
│   Frontend   │  { context, question }   │   Backend    │  ──────────────────▶ │  Claude  │
│  (Next.js)   │ ───────────────────────▶ │  (FastAPI)   │ ◀────────────────────│  (Haiku) │
│   browser    │ ◀─────────────────────── │   server     │      answer text     └──────────┘
└──────────────┘      { answer }          └──────────────┘
                                          holds the API key,
                                          validates input,
                                          builds the prompt
```

## Why a frontend *and* a backend

The whole architecture is forced by one fact: **the LLM API key cannot live in the
browser.** Anything the browser downloads, a user can read — so a key shipped to the
client is a public key that bills your account. The key therefore lives on a server
the client never sees. The browser collects input and renders the answer; the server
holds the secret, validates the request, builds the prompt, and calls the model.

## How it works

- **Input validation is declarative.** The request body is described by a Pydantic
  model, so malformed requests are rejected with a `422` before any handler runs.
  Empty/whitespace input is rejected separately with a `400` to avoid a pointless
  model call.
- **The answer is constrained to the provided context.** The system prompt instructs
  the model to use only the supplied text and to say it doesn't know otherwise — the
  cheapest available mitigation against hallucination (a reduction, not a guarantee).
- **Failures are clean.** Any upstream model error (bad key, rate limit, network) is
  caught and returned as a generic `502 { "error": ... }` — the raw exception is never
  leaked to the client.
- **Secrets stay out of the code and the image.** The key is read from the environment
  (a git-ignored `.env` locally, an injected env var in production); it is never
  hardcoded, committed, or baked into the Docker image.

### API

```
POST /ask
Request:  { "context": "<source text>", "question": "<question>" }
Response: { "answer": "<answer>" }            200
Error:    { "error":  "<reason>"  }            400 (bad input) / 502 (upstream failure)
```

## Tech choices

| Choice | Reason |
| --- | --- |
| **FastAPI** | API-only service; Pydantic gives request validation for free; async fits a workload that is mostly waiting on a slow external call. |
| **Claude Haiku** | The task is short, context-grounded Q&A, not heavy reasoning — the model is matched to the task rather than maximized by default. |
| **Docker** | Packages code + a pinned runtime + dependencies into one portable image for local/prod parity. |
| **Cloud Run** (target) | Runs the container directly and scales to zero (free when idle). The image is portable, so the host is swappable (Render, Fly, etc.). |
| **Next.js** | Minimal client — a single page with the two inputs, a loading state, and the answer. |

## Scope

Deliberately minimal. **Not** included: auth, accounts, a database, a vector store,
streaming, or chat history — the flow is stateless, so none are needed yet. The clean
extension point is retrieval: for documents larger than the context window, the
single `context` field would be replaced by chunking → embedding → vector search,
feeding only the relevant chunks to the model. That seam is intentionally left open.

## Running locally

Requires Python 3.13+, Node 18+, and an Anthropic API key.

**Backend** (http://localhost:8000):

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then put your real ANTHROPIC_API_KEY in .env
uvicorn main:app --reload --port 8000
```

**Frontend** (http://localhost:3000):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

### Run the backend in Docker

```bash
cd backend
docker build -t ask-my-docs-backend .
docker run --rm -p 8080:8080 -e ANTHROPIC_API_KEY=sk-ant-... ask-my-docs-backend
```

## Project structure

```
ask-my-docs/
├── backend/          FastAPI service
│   ├── main.py       app, /ask endpoint, validation, LLM call, error handling
│   ├── Dockerfile    containerized backend
│   ├── requirements.txt
│   └── .env.example  template for the API key (real .env is git-ignored)
└── frontend/         Next.js client
    └── app/page.tsx  the single screen
```
