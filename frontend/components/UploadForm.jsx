import { useState } from "react";

export default function UploadForm({ onUploaded }) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const upload = async (e) => {
    e.preventDefault();
    if (!file || !title) return;
    setLoading(true);
    setError("");
    const form = new FormData();
    form.append("title", title);
    form.append("file", file);
    try {
      const res = await fetch("/api/ingest", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      onUploaded(data);
      setTitle("");
      setFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="card" style={{ marginBottom: 20 }} onSubmit={upload}>
      <h2>Upload a document</h2>
      <input
        className="input"
        placeholder="Document title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        disabled={loading}
        required
      />
      <input
        type="file"
        accept=".txt,.pdf,.docx,.md"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        disabled={loading}
        style={{ marginTop: 8 }}
        required
      />
      {error && <p className="danger" style={{ marginTop: 6 }}>{error}</p>}
      <button type="submit" disabled={loading || !file || !title} className="btn">
        {loading ? "Uploading…" : "Ingest"}
      </button>
    </form>
  );
}
