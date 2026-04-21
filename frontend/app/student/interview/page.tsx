"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { Icon } from "@/components/Icon";
import { SectionCard } from "@/components/SectionCard";
import {
  APIError,
  evaluateMockInterview,
  generateMockInterview,
  getStudentSession,
  type MockInterviewAnswer,
  type MockInterviewDraft,
  type MockInterviewEvaluation,
} from "@/lib/api";

const INTERVIEW_FULL_SCORE = 100;

export default function StudentInterviewPage() {
  const [studentId, setStudentId] = useState<number | null>(null);
  const [jobCode, setJobCode] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [draft, setDraft] = useState<MockInterviewDraft | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [evaluation, setEvaluation] = useState<MockInterviewEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const session = await getStudentSession();
        setStudentId(session.student_id ?? null);
        setJobCode(session.resolved_job_code || session.target_job_code || session.suggested_job_code || "");
        setJobTitle(session.resolved_job_title || session.target_job_title || session.suggested_job_title || "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载学生信息失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const answerList = useMemo<MockInterviewAnswer[]>(
    () =>
      Object.entries(answers)
        .filter(([, answer]) => answer.trim())
        .map(([question_id, answer]) => ({ question_id, answer })),
    [answers],
  );

  async function handleGenerate() {
    if (!studentId || !jobCode) {
      setError("请先完成学生信息和目标岗位选择。");
      return;
    }
    setRunning(true);
    setError("");
    setEvaluation(null);
    try {
      const result = await generateMockInterview(studentId, jobCode);
      setDraft(result);
      setAnswers(Object.fromEntries(result.questions.map((item) => [item.question_id, ""])));
      setJobTitle(result.job_title);
    } catch (err) {
      if (err instanceof APIError) setError(err.message);
      else setError("生成模拟面试失败");
    } finally {
      setRunning(false);
    }
  }

  async function handleEvaluate() {
    if (!studentId || !jobCode || answerList.length === 0) {
      setError("请至少填写 1 道题的回答后再评估。");
      return;
    }
    setRunning(true);
    setError("");
    try {
      const result = await evaluateMockInterview(studentId, jobCode, answerList);
      setEvaluation(result);
    } catch (err) {
      if (err instanceof APIError) setError(err.message);
      else setError("模拟面试评估失败");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return (
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <SectionCard title="模拟面试">
          <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
        </SectionCard>
      </div>
    );
  }

  if (!studentId || !jobCode) {
    return (
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <EmptyState
          icon={<Icon name="chat" size={32} />}
          title="暂时无法开始模拟面试"
          description="请先补全学生信息并确定目标岗位，系统才能按岗位要求生成面试题。"
          actionLabel="去完善资料"
          actionHref="/student/info"
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24, display: "grid", gap: 20 }}>
      <SectionCard
        title="模拟面试"
        action={
          <button
            onClick={handleGenerate}
            disabled={running}
            style={{
              minHeight: 38,
              padding: "8px 18px",
              borderRadius: 8,
              border: "1px solid #0f74da",
              background: "#0f74da",
              color: "#fff",
              fontWeight: 700,
              cursor: running ? "not-allowed" : "pointer",
            }}
          >
            {running ? "处理中..." : draft ? "重新生成题目" : "开始模拟面试"}
          </button>
        }
      >
        <div style={{ display: "grid", gap: 10 }}>
          <p>目标岗位：<strong>{jobTitle || jobCode}</strong></p>
          {draft ? (
            <>
              <p>岗位准备度：<strong>{draft.readiness_score.toFixed(1)}</strong> / {INTERVIEW_FULL_SCORE} 分，当前判断为 <strong>{draft.readiness_level}</strong>。</p>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {draft.focus_summary.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          ) : (
            <p>系统会结合目标岗位、当前匹配结果和能力短板，生成 5 道针对性面试题。</p>
          )}
          {error ? <p style={{ color: "#d32f2f", margin: 0 }}>{error}</p> : null}
        </div>
      </SectionCard>

      {draft ? (
        <>
          <SectionCard title="作答区">
            <div style={{ display: "grid", gap: 18 }}>
              {draft.questions.map((item, index) => (
                <div key={item.question_id} style={{ border: "1px solid #e5e7eb", borderRadius: 14, padding: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
                    <strong>{index + 1}. {item.question}</strong>
                    <span style={{ color: "#666", fontSize: 13 }}>{item.category}</span>
                  </div>
                  <details style={{ margin: "0 0 10px", color: "#666" }}>
                    <summary style={{ cursor: "pointer", fontWeight: 700, color: "#334155" }}>
                      查看关注点和回答提示
                    </summary>
                    <div style={{ display: "grid", gap: 6, marginTop: 8, lineHeight: 1.7 }}>
                      <p style={{ margin: 0 }}>关注点：{item.focus_points.join("、")}</p>
                      <p style={{ margin: 0 }}>回答提示：{item.answer_tips.join("；")}</p>
                    </div>
                  </details>
                  <textarea
                    value={answers[item.question_id] || ""}
                    onChange={(e) => setAnswers((prev) => ({ ...prev, [item.question_id]: e.target.value }))}
                    rows={5}
                    style={{
                      width: "100%",
                      borderRadius: 12,
                      border: "1px solid #d0d7de",
                      padding: 12,
                      resize: "vertical",
                      font: "inherit",
                    }}
                    placeholder="在这里输入你的回答"
                  />
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16 }}>
              <button
                onClick={handleEvaluate}
                disabled={running}
                style={{
                  padding: "10px 16px",
                  borderRadius: 10,
                  border: "none",
                  background: "#111827",
                  color: "#fff",
                  cursor: running ? "not-allowed" : "pointer",
                }}
              >
                {running ? "评估中..." : "提交并评估"}
              </button>
            </div>
          </SectionCard>

          {evaluation ? (
            <>
              <SectionCard title="评估结果">
                <div style={{ display: "grid", gap: 10 }}>
                  <p>综合得分：<strong>{evaluation.overall_score.toFixed(1)}</strong> / {INTERVIEW_FULL_SCORE} 分</p>
                  <p>面试准备度：<strong>{evaluation.readiness_level}</strong></p>
                  <p>{evaluation.recommendation}</p>
                </div>
              </SectionCard>

              <SectionCard title="逐题反馈">
                <div style={{ display: "grid", gap: 16 }}>
                  {evaluation.feedback.map((item) => (
                    <div key={item.question_id} style={{ border: "1px solid #e5e7eb", borderRadius: 14, padding: 16 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
                        <strong>{item.question}</strong>
                        <span style={{ color: item.score >= 80 ? "#2e7d32" : item.score >= 70 ? "#ef6c00" : "#c62828", fontWeight: 700 }}>
                          {item.score.toFixed(1)} / {INTERVIEW_FULL_SCORE} 分
                        </span>
                      </div>
                      <p style={{ margin: "0 0 6px" }}>命中要点：{item.matched_points.length ? item.matched_points.join("、") : "暂无"}</p>
                      <p style={{ margin: "0 0 6px" }}>缺失要点：{item.missing_points.length ? item.missing_points.join("、") : "无明显缺失"}</p>
                      <p style={{ margin: 0 }}>改进建议：{item.suggestion}</p>
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="下一步建议">
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {evaluation.next_actions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </SectionCard>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
