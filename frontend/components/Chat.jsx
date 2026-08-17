"use client";

import { useState } from "react";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const ask = async (q) => {
    setLoading(true);
    setMessages((m) => [...m, { role: "user", content: q }]);
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      setMessages((m) => [
        ...m,
        { role: "assistant", content: data.answer || "No answer returned." },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Error: " + (e.message || "try again") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) ask(input.trim());
    setInput("");
  };

  return (
    <div className="chat-wrap card">
      <h2>Ask a question</h2>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div
            key={i}
            className={m.role === "user" ? "bubble user" : "bubble assistant"}
          >
            {m.content}
          </div>
        ))}
        {loading && <div className="bubble assistant">Thinking…</div>}
      </div>
      <form className="chat-form" onSubmit={onSubmit}>
        <input
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something about the uploaded document…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn">
          Send
        </button>
      </form>
    </div>
  );
}
