"use client";

import { useEffect, useMemo, useState } from "react";
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
  onSkip?: () => void;
  onCancel?: () => void;
};

const COLLAPSED_JOB_COUNT = 12;

export function JobSelector({ onSelect, onSkip, onCancel }: Props) {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    getJobTemplates()
      .then((data) => setJobs(data as unknown as JobItem[]))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  const jobOptions = useMemo(
    () =>
      jobs.map((job, index) => ({
        job,
        code: job.job_code || `J-SEL-${index}`,
        label: job.industry || job.category || "",
      })),
    [jobs],
  );

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredJobs = useMemo(() => {
    if (!normalizedQuery) return jobOptions;
    return jobOptions.filter(({ job, code, label }) => {
      const searchable = [job.title, label, job.category, job.industry, code]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return searchable.includes(normalizedQuery);
    });
  }, [jobOptions, normalizedQuery]);

  const visibleJobs =
    expanded || normalizedQuery
      ? filteredJobs
      : filteredJobs.slice(0, COLLAPSED_JOB_COUNT);
  const hiddenCount = Math.max(filteredJobs.length - visibleJobs.length, 0);
  const selectedJob = jobOptions.find((option) => option.code === selected);

  if (loading) {
    return (
      <div className="job-selector">
        <p className="job-selector__hint">加载岗位列表中...</p>
      </div>
    );
  }

  return (
    <div className="job-selector">
      <div className="job-selector__header">
        <div>
          <p className="job-selector__hint">请先选择一个目标岗位，再开始分析：</p>
          <p className="job-selector__hint">如果暂时不确定方向，也可以先解析简历，由系统推荐适合岗位。</p>
          <p className="job-selector__summary">
            共 {jobs.length} 个岗位{normalizedQuery ? `，匹配 ${filteredJobs.length} 个` : ""}
          </p>
        </div>
        {filteredJobs.length > COLLAPSED_JOB_COUNT && !normalizedQuery && (
          <button
            type="button"
            className="job-selector__fold"
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? "收起" : `展开更多 ${hiddenCount}`}
          </button>
        )}
      </div>

      <label className="job-selector__search">
        <span className="job-selector__search-label">搜索岗位</span>
        <input
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="输入岗位名称、行业或类别"
          aria-label="搜索岗位"
        />
      </label>

      <div className="job-selector__grid">
        {visibleJobs.map(({ job, code, label }) => {
          return (
            <button
              key={code}
              type="button"
              className={`job-selector__card ${selected === code ? "job-selector__card--active" : ""}`}
              onClick={() => setSelected(selected === code ? null : code)}
            >
              <span className="job-selector__title">{job.title}</span>
              {label && <span className="job-selector__tag">{label}</span>}
            </button>
          );
        })}
      </div>

      {filteredJobs.length === 0 && (
        <p className="job-selector__empty">没有找到匹配的岗位，请换个关键词试试。</p>
      )}

      <div className="job-selector__actions">
        <span className="job-selector__selected">
          {selectedJob ? `已选择：${selectedJob.job.title}` : "请选择一个岗位"}
        </span>
        {onCancel && (
          <button
            type="button"
            className="job-selector__back"
            onClick={onCancel}
          >
            返回上传
          </button>
        )}
        {onSkip && (
          <button
            type="button"
            className="job-selector__skip"
            onClick={onSkip}
          >
            暂不选择，先分析简历
          </button>
        )}
        <button
          type="button"
          className="job-selector__confirm btn-primary"
          disabled={!selected}
          onClick={() => {
            if (selected && selectedJob) {
              onSelect(selected, selectedJob.job.title);
            }
          }}
        >
          确认选择并开始分析
        </button>
      </div>
      <style jsx>{`
        .job-selector {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 18px 20px;
          margin-bottom: 16px;
        }
        .job-selector__header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 14px;
        }
        .job-selector__hint {
          font-size: 14px;
          color: #666;
          margin: 0;
        }
        .job-selector__summary {
          margin: 6px 0 0;
          font-size: 12px;
          color: #8a94a6;
        }
        .job-selector__fold {
          flex-shrink: 0;
          min-height: 34px;
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          background: #fff;
          color: #173f8a;
          box-shadow: none;
          filter: none;
        }
        .job-selector__fold:hover {
          background: #f8fafc;
          box-shadow: none;
          filter: none;
          transform: none;
        }
        .job-selector__search {
          display: grid;
          grid-template-columns: auto minmax(220px, 1fr);
          align-items: center;
          gap: 12px;
          margin-bottom: 14px;
        }
        .job-selector__search-label {
          font-size: 13px;
          font-weight: 600;
          color: #334155;
          white-space: nowrap;
        }
        .job-selector__search input {
          min-height: 38px;
          padding: 8px 12px;
          border-radius: 8px;
          border: 1px solid #d1d5db;
          font-size: 14px;
          background: #fff;
        }
        .job-selector__grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin-bottom: 14px;
        }
        .job-selector__card {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          min-height: 52px;
          padding: 9px 12px;
          cursor: pointer;
          background: #fff;
          text-align: center;
          transition: all 0.15s;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 6px;
          box-shadow: none;
          filter: none;
        }
        .job-selector__card:hover {
          border-color: #2563eb;
          box-shadow: none;
          filter: none;
        }
        .job-selector__card--active {
          border-color: #2563eb;
          background: #eff6ff;
        }
        .job-selector__title {
          font-size: 14px;
          font-weight: 500;
          color: #111;
          line-height: 1.25;
        }
        .job-selector__tag {
          font-size: 12px;
          color: #888;
          line-height: 1.2;
        }
        .job-selector__empty {
          margin: 0 0 14px;
          padding: 12px;
          border: 1px dashed #d1d5db;
          border-radius: 8px;
          color: #64748b;
          text-align: center;
          font-size: 13px;
        }
        .job-selector__actions {
          display: flex;
          gap: 10px;
          align-items: center;
          justify-content: flex-end;
          margin-top: 4px;
          flex-wrap: wrap;
        }
        .job-selector__selected {
          margin-right: auto;
          color: #475569;
          font-size: 13px;
        }
        .job-selector__back {
          font-size: 14px;
          color: #666;
          background: none;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          padding: 8px 16px;
          cursor: pointer;
          min-height: 36px;
          transition: all 0.15s;
        }
        .job-selector__back:hover {
          background: #f9fafb;
          border-color: #9ca3af;
        }
        .job-selector__skip {
          font-size: 14px;
          color: #0f766e;
          background: #f0fdfa;
          border: 1px solid #99f6e4;
          border-radius: 8px;
          padding: 8px 16px;
          cursor: pointer;
          min-height: 36px;
          transition: all 0.15s;
        }
        .job-selector__skip:hover {
          background: #ccfbf1;
          border-color: #5eead4;
        }
        .job-selector__confirm {
          margin-top: 0;
        }
        .job-selector__confirm:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        @media (max-width: 640px) {
          .job-selector {
            padding: 16px;
          }
          .job-selector__header,
          .job-selector__search {
            grid-template-columns: 1fr;
          }
          .job-selector__header {
            display: grid;
          }
          .job-selector__fold {
            justify-self: start;
          }
          .job-selector__grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
          .job-selector__actions {
            align-items: stretch;
          }
          .job-selector__selected,
          .job-selector__back,
          .job-selector__skip,
          .job-selector__confirm {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
