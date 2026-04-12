"use client";

import { useEffect, useState } from "react";
import { getJobTemplates } from "@/lib/api";

type JobItem = {
  job_code?: string;
  title: string;
  industry?: string;
  category?: string;
  [key: string]: unknown;
};

type Props = {
  onSelect: (jobCode: string, jobTitle: string) => void;
};

export function JobSelector({ onSelect }: Props) {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    getJobTemplates()
      .then((data) => setJobs(data as unknown as JobItem[]))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="job-selector">
        <p className="job-selector__hint">加载岗位列表中...</p>
      </div>
    );
  }

  return (
    <div className="job-selector">
      <p className="job-selector__hint">请先选择一个目标岗位，再开始分析：</p>
      <div className="job-selector__grid">
        {jobs.map((job, i) => {
          const code = job.job_code || `J-SEL-${i}`;
          const label = job.industry || job.category || "";
          return (
            <button
              key={code}
              className={`job-selector__card ${selected === code ? "job-selector__card--active" : ""}`}
              onClick={() => setSelected(code)}
            >
              <span className="job-selector__title">{job.title}</span>
              {label && <span className="job-selector__tag">{label}</span>}
            </button>
          );
        })}
      </div>
      <button
        className="job-selector__confirm btn-primary"
        disabled={!selected}
        onClick={() => {
          if (selected) {
            const job = jobs.find((j) => (j.job_code || "") === selected);
            onSelect(selected, job?.title ?? selected);
          }
        }}
      >
        确认选择并开始分析
      </button>
      <style jsx>{`
        .job-selector {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 20px 24px;
          margin-bottom: 16px;
        }
        .job-selector__hint {
          font-size: 14px;
          color: #666;
          margin-bottom: 16px;
        }
        .job-selector__grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 10px;
          margin-bottom: 16px;
        }
        .job-selector__card {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 12px 14px;
          cursor: pointer;
          background: #fff;
          text-align: left;
          transition: all 0.15s;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .job-selector__card:hover {
          border-color: #2563eb;
        }
        .job-selector__card--active {
          border-color: #2563eb;
          background: #eff6ff;
        }
        .job-selector__title {
          font-size: 14px;
          font-weight: 500;
          color: #111;
        }
        .job-selector__tag {
          font-size: 12px;
          color: #888;
        }
        .job-selector__confirm {
          margin-top: 4px;
        }
        .job-selector__confirm:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
