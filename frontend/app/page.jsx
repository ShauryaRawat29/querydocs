"use client";

import { useState } from "react";
import Chat from "../components/Chat";
import UploadForm from "../components/UploadForm";

export default function Page() {
  const [doc, setDoc] = useState(null);
  return (
    <>
      <h1>QueryDocs — Ask your documents</h1>
      <p className="text-muted">
        Upload a PDF/TXT/MD/DOCX, then ask questions. Answers are grounded in
        your document; no AI verdicts, just cited evidence.
      </p>
      <UploadForm onUploaded={(r) => setDoc({ title: r.title, chunks: r.chunks })} />
      {doc && (
        <p className="success" style={{ marginTop: 6 }}>
          Ingested "{doc.title}" ({doc.chunks} chunks). Ask below.
        </p>
      )}
      <div style={{ marginTop: 24 }}>
        <Chat />
      </div>
    </>
  );
}
