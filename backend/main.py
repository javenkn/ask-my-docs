import os

import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Load a local .env file into os.environ if one exists. In production (Cloud Run)
# there is no .env file, so this is a harmless no-op and the real injected env
# vars are used. This must run BEFORE we read ANTHROPIC_API_KEY below.
load_dotenv()

# Fail fast: the SDK's Anthropic() does NOT raise on a missing key (it lazily
# fails at call time), so we check ourselves. Better to crash loudly at startup
# than to boot fine and 502 on the first real request.
if not os.environ.get("ANTHROPIC_API_KEY"):
    raise RuntimeError("ANTHROPIC_API_KEY is not set")

app = FastAPI()

# CORS: the browser blocks cross-origin reads unless the SERVER grants permission.
# This middleware answers the preflight OPTIONS request and adds the
# Access-Control-Allow-* headers. We allow ONLY our known frontend origin (not "*")
# — least privilege. When we deploy, the deployed frontend's URL gets added here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# Build the client once at startup. Anthropic() reads ANTHROPIC_API_KEY from the
# environment — the secret never appears in this source file and never reaches
# the browser.
client = Anthropic()

# The model id is the exact string — no date suffix. Haiku is the cheapest/
# fastest tier; chosen deliberately because the task is short, context-grounded
# Q&A, not hard reasoning. Swap to "claude-opus-4-8" if answers need more depth.
MODEL = "claude-haiku-4-5"

# The product promise is "answers about YOUR doc", so we constrain the model to
# the supplied context. The explicit "say you don't know" is the cheapest
# hallucination mitigation — it reduces, but does not eliminate, made-up answers.
SYSTEM_PROMPT = (
    "Answer the user's question using ONLY the provided context. "
    "If the answer is not contained in the context, say you don't know. "
    "Do not use any outside knowledge."
)


class AskRequest(BaseModel):
    context: str
    question: str


@app.post("/ask")
def ask(payload: AskRequest):
    # Pydantic guaranteed these are present strings, but "present" isn't
    # "meaningful" — empty or whitespace-only input is junk we reject ourselves.
    # JSONResponse (not HTTPException) so the body matches our {"error": ...}
    # contract instead of FastAPI's default {"detail": ...}.
    if not payload.context.strip() or not payload.question.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "context and question must both be non-empty"},
        )

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{payload.context}\n\nQuestion: {payload.question}",
                }
            ],
        )
    except anthropic.APIError:
        # Any upstream failure (bad key, rate limit, network, 5xx) lands here.
        # Return a clean error; never leak the raw exception to the client.
        return JSONResponse(
            status_code=502,
            content={"error": "failed to get an answer from the language model"},
        )

    # response.content is a LIST of content blocks, not a string. Pull the text
    # out of the text block(s) and join them.
    answer = "".join(block.text for block in message.content if block.type == "text")
    return {"answer": answer}
