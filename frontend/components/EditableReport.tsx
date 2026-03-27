"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export function EditableReport({
  initialMarkdown
}: {
  initialMarkdown: string;
}) {
  const [content, setContent] = useState(initialMarkdown);
  const [status, setStatus] = useState("可编辑草稿");

  const polish = async () => {
    try {
      const response = await fetch(`${API_BASE}/reports/polish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: 1, markdown_content: content })
      });
      const data = await response.json();
      setContent(data.markdown_content ?? content);
      setStatus("已完成智能润色");
    } catch {
      setStatus("后端未连接，保留当前草稿");
    }
  };

  const exportFile = async (format: "pdf" | "docx") => {
    try {
      const response = await fetch(`${API_BASE}/reports/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: 1, format })
      });
      const data = await response.json();
      setStatus(`${format.toUpperCase()} 已导出：${data.exported?.file_name ?? "完成"}`);
    } catch {
      setStatus(`后端未连接，${format.toUpperCase()} 导出未执行`);
    }
  };

  return (
    <div className="report-editor">
      <div className="editor-toolbar">
        <button onClick={polish}>智能润色</button>
        <button onClick={() => exportFile("pdf")}>导出 PDF</button>
        <button onClick={() => exportFile("docx")}>导出 DOCX</button>
        <span>{status}</span>
      </div>
      <textarea value={content} onChange={(event) => setContent(event.target.value)} />
    </div>
  );
}

