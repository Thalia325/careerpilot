"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { startTransition, useMemo, useRef, useState } from "react";

type AgentComposerProps = {
  roleTags: string[];
};

const ALLOWED_TYPES = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/png", "image/jpeg"];
const ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function AgentComposer({ roleTags }: AgentComposerProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [fileName, setFileName] = useState("");
  const [fileError, setFileError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const canStart = useMemo(() => Boolean(query.trim() || fileName), [fileName, query]);
  const charCount = query.length;

  const openFilePicker = () => fileInputRef.current?.click();

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

  const handleFile = (file?: File) => {
    if (!file) {
      return;
    }

    const error = validateFile(file);
    if (error) {
      setFileError(error);
      setFileName("");
      return;
    }

    setFileError("");
    setFileName(file.name);
  };

  const handleStart = () => {
    const params = new URLSearchParams();
    if (query.trim()) {
      params.set("query", query.trim());
    }
    if (fileName) {
      params.set("resume", fileName);
    }
    startTransition(() => {
      router.push(`/workspace${params.toString() ? `?${params.toString()}` : ""}`);
    });
  };

  return (
    <div className="agent-composer">
      <div
        className={`agent-composer__upload ${isDragging ? "is-dragging" : ""}`}
        onClick={openFilePicker}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFile(event.dataTransfer.files?.[0]);
        }}
      >
        <input
          ref={fileInputRef}
          hidden
          type="file"
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
          onChange={(event) => handleFile(event.target.files?.[0] ?? undefined)}
        />
        <div>
          <p className="agent-composer__upload-title">{fileName || "上传简历或拖拽文件到这里"}</p>
          <p className="agent-composer__upload-note">支持 PDF、DOCX、图片。也可以先只输入目标岗位。</p>
          {fileError && <p className="agent-composer__upload-error">{fileError}</p>}
        </div>
        <button type="button" className="agent-composer__upload-button">
          选择文件
        </button>
      </div>

      <label className="agent-composer__field" htmlFor="query-textarea">
        <span>目标岗位 / 想咨询的问题</span>
        <textarea
          id="query-textarea"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="上传简历，或输入你想了解的岗位方向"
          maxLength={500}
        />
        <div className="agent-composer__char-count">{charCount}/500</div>
      </label>

      <div className="agent-composer__tags">
        {roleTags.map((tag) => (
          <button key={tag} type="button" className="agent-composer__tag" onClick={() => setQuery(tag)}>
            {tag}
          </button>
        ))}
      </div>

      <div className="agent-composer__actions">
        <button type="button" onClick={handleStart} disabled={!canStart} className="agent-composer__primary">
          开始分析
        </button>
        <Link href="/results/report-sample" className="agent-composer__secondary">
          查看示例报告
        </Link>
      </div>
    </div>
  );
}

