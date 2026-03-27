"use client";

import { useState, startTransition } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export function UploadLab() {
  const [rawText, setRawText] = useState(
    "姓名：陈同学\n专业：软件工程\n技能：JavaScript TypeScript React Next.js Python FastAPI SQL\n项目：CareerPilot 职业规划系统\n实习：教育科技公司前端开发实习生\n证书：英语四级 计算机二级\nGPA：3.7"
  );
  const [result, setResult] = useState<string>("点击“模拟 OCR 解析”后，将展示结构化输出。");
  const [isLoading, setIsLoading] = useState(false);

  const handleParse = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/ocr/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: rawText, document_type: "resume" })
      });
      const data = await response.json();
      startTransition(() => {
        setResult(JSON.stringify(data.structured_json ?? data, null, 2));
      });
    } catch {
      setResult("后端未连接，当前展示本地 demo 模式。你仍然可以继续查看后续页面。");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-grid">
      <textarea value={rawText} onChange={(event) => setRawText(event.target.value)} />
      <div className="upload-output">
        <button onClick={handleParse} disabled={isLoading}>
          {isLoading ? "解析中..." : "模拟 OCR 解析"}
        </button>
        <pre>{result}</pre>
      </div>
    </div>
  );
}

