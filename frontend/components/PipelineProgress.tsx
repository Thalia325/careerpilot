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

const statusIcon: Record<PipelineStepStatus, string> = {
  pending: "\u25CB",
  running: "\u25B3",
  done: "\u2705",
  error: "\u274C",
};

const statusColor: Record<PipelineStepStatus, string> = {
  pending: "#aaa",
  running: "#2563eb",
  done: "#16a34a",
  error: "#dc2626",
};

export function PipelineProgress({ steps, onRetry }: Props) {
  return (
    <div className="pipeline-progress">
      <div className="pipeline-progress__title">分析进度</div>
      <div className="pipeline-progress__steps">
        {steps.map((step, i) => (
          <div key={step.key} className="pipeline-progress__step">
            <div className="pipeline-progress__step-left">
              <span
                className="pipeline-progress__icon"
                style={{ color: statusColor[step.status] }}
              >
                {step.status === "running" ? (
                  <span className="pipeline-progress__spinner" />
                ) : (
                  statusIcon[step.status]
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
              {step.detail && (
                <span className="pipeline-progress__detail">{step.detail}</span>
              )}
              {step.status === "error" && onRetry && (
                <button
                  className="pipeline-progress__retry"
                  onClick={() => onRetry(step.key)}
                >
                  重试
                </button>
              )}
            </div>
          </div>
        ))}
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
        }
        .pipeline-progress__step-left {
          display: flex;
          align-items: center;
          width: 100%;
          position: relative;
          justify-content: center;
        }
        .pipeline-progress__icon {
          font-size: 18px;
          z-index: 1;
          background: #fff;
          padding: 0 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
        }
        .pipeline-progress__spinner {
          display: inline-block;
          width: 18px;
          height: 18px;
          border: 2px solid #e5e7eb;
          border-top-color: #2563eb;
          border-radius: 50%;
          animation: pipeline-spin 0.8s linear infinite;
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
          font-weight: 500;
          white-space: nowrap;
        }
        .pipeline-progress__detail {
          font-size: 11px;
          color: #888;
        }
        .pipeline-progress__retry {
          font-size: 12px;
          color: #2563eb;
          background: none;
          border: 1px solid #2563eb;
          border-radius: 4px;
          padding: 2px 10px;
          cursor: pointer;
          margin-top: 4px;
        }
        .pipeline-progress__retry:hover {
          background: #eff6ff;
        }
      `}</style>
    </div>
  );
}
