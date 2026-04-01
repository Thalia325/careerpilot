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
  const [isSaving, setIsSaving] = useState(false);
  const [isExportingPDF, setIsExportingPDF] = useState(false);
  const [isExportingDOCX, setIsExportingDOCX] = useState(false);

  const saveContent = async () => {
    setIsSaving(true);
    try {
      const response = await fetch(`${API_BASE}/reports/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: 1, markdown_content: content })
      });

      if (!response.ok) {
        throw new Error("保存失败");
      }

      setStatus("已保存");
      setTimeout(() => setStatus("可编辑草稿"), 3000);
    } catch {
      setStatus("保存失败，请重试");
    } finally {
      setIsSaving(false);
    }
  };

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
    const isExportingPDFLocal = format === "pdf";
    if (isExportingPDFLocal) {
      setIsExportingPDF(true);
    } else {
      setIsExportingDOCX(true);
    }

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
    } finally {
      if (isExportingPDFLocal) {
        setIsExportingPDF(false);
      } else {
        setIsExportingDOCX(false);
      }
    }
  };

  return (
    <div className="report-editor">
      <div className="editor-toolbar">
        <button
          onClick={saveContent}
          disabled={isSaving}
          aria-label="保存报告内容"
        >
          {isSaving ? "保存中..." : "保存"}
        </button>
        <button onClick={polish} aria-label="使用 AI 智能润色报告内容">
          智能润色
        </button>
        <button
          onClick={() => exportFile("pdf")}
          disabled={isExportingPDF}
          aria-label="将报告导出为 PDF 格式"
        >
          {isExportingPDF ? "导出中..." : "导出 PDF"}
        </button>
        <button
          onClick={() => exportFile("docx")}
          disabled={isExportingDOCX}
          aria-label="将报告导出为 Word 文档格式"
        >
          {isExportingDOCX ? "导出中..." : "导出 DOCX"}
        </button>
        <span role="status" aria-live="polite">
          {status}
        </span>
      </div>
      <textarea
        value={content}
        onChange={(event) => setContent(event.target.value)}
        aria-label="职业规划报告内容编辑区域"
        placeholder="在这里编辑你的职业规划报告..."
      />
    </div>
  );
}

