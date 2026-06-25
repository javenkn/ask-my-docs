"use client";

import { useState } from "react";

// The backend's address. Hardcoded for local dev; we'll move this to an
// environment variable when we deploy (the deployed backend has a different URL).
const BACKEND_URL = "http://localhost:8000/ask";

export default function Home() {
  const [context, setContext] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    // Reset previous results, flip into loading state.
    setAnswer("");
    setError("");
    setLoading(true);

    try {
      const res = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context, question }),
      });

      const data = await res.json();

      // Honor the backend contract: success -> {answer}, failure -> {error}.
      if (res.ok) {
        setAnswer(data.answer);
      } else {
        setError(data.error ?? "Something went wrong.");
      }
    } catch {
      // This catch fires on a NETWORK-level failure — including, as we're about
      // to discover, the browser blocking the response for CORS reasons.
      setError("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "40px auto", padding: "0 16px", fontFamily: "sans-serif" }}>
      <h1>Ask My Docs</h1>

      <label>
        Context
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          rows={8}
          style={{ width: "100%", display: "block", marginBottom: 12 }}
          placeholder="Paste the source text here..."
        />
      </label>

      <label>
        Question
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={2}
          style={{ width: "100%", display: "block", marginBottom: 12 }}
          placeholder="Ask something about the context above..."
        />
      </label>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Asking..." : "Ask"}
      </button>

      {answer && (
        <div style={{ marginTop: 20, whiteSpace: "pre-wrap" }}>
          <strong>Answer:</strong>
          <p>{answer}</p>
        </div>
      )}

      {error && (
        <div style={{ marginTop: 20, color: "crimson" }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </main>
  );
}
