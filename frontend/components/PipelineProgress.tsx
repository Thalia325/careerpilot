"use client";

export type PipelineStepStatus = "pending" | "running" | "done" | "error";

export type PipelineStep = {
  key: string;
  label: string;
  status: PipelineStepStatus;
  detail?: string;
};

type Props = {
  steps: PipelineStep[];
  onRetry?: (key: string) => void;
};

const statusColor: Record<PipelineStepStatus, string> = {
  pending: "#9ca3af",
  running: "#2563eb",
  done: "#16a34a",
  error: "#dc2626",
};

const statusLabel: Record<PipelineStepStatus, string> = {
  pending: "待开始",
  running: "进行中",
  done: "已完成",
  error: "失败",
};

export function PipelineProgress({ steps, onRetry }: Props) {
  return (
    <div className="pipeline-progress">
      <div className="pipeline-progress__title">分析进度</div>
      <div className="pipeline-progress__steps">
        {steps.map((step, i) => {
          const isRunning = step.status === "running";
          const isError = step.status === "error";
          return (
            <div
              key={step.key}
              className={`pipeline-progress__step${isRunning ? " is-running" : ""}${isError ? " is-error" : ""}`}
            >
              <div className="pipeline-progress__step-left">
                <span
                  className={`pipeline-progress__icon pipeline-progress__icon--${step.status}`}
                >
                  {isRunning ? (
                    <span className="pipeline-progress__spinner" />
                  ) : step.status === "done" ? (
                    <span className="pipeline-progress__check">&#10003;</span>
                  ) : step.status === "error" ? (
                    <span className="pipeline-progress__cross">&#10007;</span>
                  ) : (
                    <span className="pipeline-progress__circle" />
                  )}
                </span>
                {i < steps.length - 1 && (
                  <span
                    className="pipeline-progress__line"
                    style={{
                      backgroundColor:
                        step.status === "done" ? statusColor.done : "#e5e7eb",
                    }}
                  />
                )}
              </div>
              <div className="pipeline-progress__step-right">
                <span
                  className="pipeline-progress__label"
                  style={{ color: statusColor[step.status] }}
                >
                  {step.label}
                </span>
                <span
                  className={`pipeline-progress__status-badge pipeline-progress__status-badge--${step.status}`}
                >
                  {statusLabel[step.status]}
                </span>
                {isError && step.detail && (
                  <span className="pipeline-progress__error-detail">{step.detail}</span>
                )}
                {isError && onRetry && (
                  <button
                    className="pipeline-progress__retry"
                    onClick={() => onRetry(step.key)}
                  >
                    重试此步骤
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <style jsx>{`
        .pipeline-progress {
          background: #fff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 20px 24px;
          margin-bottom: 16px;
        }
        .pipeline-progress__title {
          font-weight: 600;
          font-size: 15px;
          margin-bottom: 16px;
          color: #111;
        }
        .pipeline-progress__steps {
          display: flex;
          gap: 0;
        }
        .pipeline-progress__step {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex: 1;
          position: relative;
          min-width: 0;
          border-radius: 10px;
          padding: 8px 4px 10px;
          transition: background 0.25s ease;
        }
        .pipeline-progress__step.is-running {
          background: rgba(37, 99, 235, 0.06);
        }
        .pipeline-progress__step.is-error {
          background: rgba(220, 38, 38, 0.05);
        }
        .pipeline-progress__step-left {
          display: flex;
          align-items: center;
          width: 100%;
          position: relative;
          justify-content: center;
        }
        .pipeline-progress__icon {
          font-size: 16px;
          z-index: 1;
          background: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
        }
        .pipeline-progress__icon--pending .pipeline-progress__circle {
          display: block;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          border: 2px solid #d1d5db;
        }
        .pipeline-progress__icon--running .pipeline-progress__spinner {
          display: inline-block;
          width: 20px;
          height: 20px;
          border: 2.5px solid #dbeafe;
          border-top-color: #2563eb;
          border-radius: 50%;
          animation: pipeline-spin 0.75s linear infinite;
        }
        .pipeline-progress__icon--done .pipeline-progress__check {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: #16a34a;
          color: #fff;
          font-size: 13px;
          font-weight: 700;
        }
        .pipeline-progress__icon--error .pipeline-progress__cross {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: #dc2626;
          color: #fff;
          font-size: 13px;
          font-weight: 700;
        }
        @keyframes pipeline-spin {
          to {
            transform: rotate(360deg);
          }
        }
        .pipeline-progress__line {
          position: absolute;
          top: 50%;
          left: calc(50% + 18px);
          right: calc(-50% + 18px);
          height: 2px;
          z-index: 0;
        }
        .pipeline-progress__step-right {
          margin-top: 8px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .pipeline-progress__label {
          font-size: 13px;
          font-weight: 600;
          white-space: nowrap;
        }
        .pipeline-progress__status-badge {
          font-size: 11px;
          font-weight: 600;
          padding: 1px 8px;
          border-radius: 99px;
          white-space: nowrap;
        }
        .pipeline-progress__status-badge--pending {
          background: #f3f4f6;
          color: #9ca3af;
        }
        .pipeline-progress__status-badge--running {
          background: #dbeafe;
          color: #2563eb;
          animation: pipeline-pulse 1.5s ease-in-out infinite;
        }
        @keyframes pipeline-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        .pipeline-progress__status-badge--done {
          background: #dcfce7;
          color: #16a34a;
        }
        .pipeline-progress__status-badge--error {
          background: #fee2e2;
          color: #dc2626;
        }
        .pipeline-progress__error-detail {
          font-size: 12px;
          color: #b91c1c;
          max-width: 140px;
          word-break: break-all;
          line-height: 1.4;
        }
        .pipeline-progress__retry {
          font-size: 12px;
          color: #2563eb;
          background: none;
          border: 1px solid #2563eb;
          border-radius: 6px;
          padding: 3px 12px;
          cursor: pointer;
          margin-top: 4px;
          min-height: 28px;
          font-weight: 600;
        }
        .pipeline-progress__retry:hover {
          background: #eff6ff;
        }

        @media (max-width: 640px) {
          .pipeline-progress {
            padding: 14px 12px;
          }
          .pipeline-progress__step {
            padding: 6px 2px 8px;
          }
          .pipeline-progress__label {
            font-size: 11px;
          }
          .pipeline-progress__status-badge {
            font-size: 10px;
            padding: 1px 6px;
          }
          .pipeline-progress__error-detail {
            font-size: 11px;
            max-width: 100px;
          }
        }
      `}</style>
    </div>
  );
}
