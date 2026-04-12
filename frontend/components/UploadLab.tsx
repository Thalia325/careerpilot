"use client";

import { useState, startTransition } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const ALLOWED_TYPES = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/png", "image/jpeg"];
const ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function UploadLab() {
  const [rawText, setRawText] = useState("");
  const [result, setResult] = useState<string>("点击'智能识别文档'后，将展示结构化输出。");
  const [isLoading, setIsLoading] = useState(false);
  const [fileError, setFileError] = useState("");

  const validateFile = (file: File): string => {
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext))) {
      return "不支持的文件类型。请上传 PDF、DOCX、PNG 或 JPG 文件。";
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `文件过大。请上传不超过 10MB 的文件（当前：${(file.size / 1024 / 1024).toFixed(2)}MB）。`;
    }

    return "";
  };

  const handleParse = async () => {
    setIsLoading(true);
    setFileError("");
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const response = await fetch(`${API_BASE}/ocr/parse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ raw_text: rawText, document_type: "resume" })
      });
      const data = await response.json();
      startTransition(() => {
        setResult(JSON.stringify(data.structured_json ?? data, null, 2));
      });
    } catch {
      setResult("服务暂时不可用，正在使用本地演示模式。你仍然可以继续查看后续页面。");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-grid">
      <textarea
        value={rawText}
        onChange={(event) => setRawText(event.target.value)}
        aria-label="输入文本内容以进行智能识别"
        placeholder="请输入要识别的文本内容..."
      />
      <div className="upload-output">
        <button
          onClick={handleParse}
          disabled={isLoading}
          aria-label={isLoading ? "正在识别文档中" : "点击智能识别文档"}
        >
          {isLoading ? "识别中..." : "智能识别文档"}
        </button>
        <pre role="region" aria-label="识别结果输出" aria-live="polite">
          {result}
        </pre>
      </div>
    </div>
  );
}
