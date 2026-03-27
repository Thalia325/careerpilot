"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { startTransition, useMemo, useRef, useState } from "react";

type AgentComposerProps = {
  roleTags: string[];
};

export function AgentComposer({ roleTags }: AgentComposerProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [fileName, setFileName] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const canStart = useMemo(() => Boolean(query.trim() || fileName), [fileName, query]);

  const openFilePicker = () => fileInputRef.current?.click();

  const handleFile = (file?: File) => {
    if (!file) {
      return;
    }
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
        </div>
        <button type="button" className="agent-composer__upload-button">
          选择文件
        </button>
      </div>

      <label className="agent-composer__field">
        <span>目标岗位 / 想咨询的问题</span>
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="上传简历，或输入你想了解的岗位方向"
        />
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

