import { demoJobTemplates, demoMatching, demoPath, demoReportMarkdown, demoStudentProfile } from "./demo-data";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export type StudentProfile = typeof demoStudentProfile;
export type MatchingResult = typeof demoMatching;
export type PathPlan = typeof demoPath;
export type SchedulerJobItem = {
  job_name: string;
  cron_expr: string;
  status: string;
  job_type: string;
};
export type ReportDraft = {
  report_id: number;
  student_id: number;
  job_code: string;
  markdown_content: string;
  content: Record<string, unknown>;
  status: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getStudentProfile(): Promise<StudentProfile> {
  try {
    return await request<StudentProfile>("/student-profiles/1");
  } catch {
    return demoStudentProfile;
  }
}

export async function getMatching(): Promise<MatchingResult> {
  try {
    return await request<MatchingResult>("/matching/analyze", {
      method: "POST",
      body: JSON.stringify({ student_id: 1, job_code: "J-FE-001" })
    });
  } catch {
    return demoMatching;
  }
}

export async function getPathPlan(): Promise<PathPlan> {
  try {
    const response = await request<{ data: PathPlan }>("/career-paths/plan", {
      method: "POST",
      body: JSON.stringify({ student_id: 1, job_code: "J-FE-001" })
    });
    return response.data;
  } catch {
    return demoPath;
  }
}

export async function getJobTemplates(): Promise<Array<{ title: string }>> {
  try {
    const response = await request<{ data: Array<{ title: string }> }>("/jobs/profiles/templates");
    return response.data;
  } catch {
    return demoJobTemplates.map((title) => ({ title }));
  }
}

export async function generateDemoReport(): Promise<ReportDraft> {
  try {
    return await request<ReportDraft>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({ student_id: 1, job_code: "J-FE-001" })
    });
  } catch {
    return {
      report_id: 1,
      student_id: 1,
      job_code: "J-FE-001",
      markdown_content: demoReportMarkdown,
      content: {},
      status: "draft"
    };
  }
}

export async function getSchedulerJobs(): Promise<SchedulerJobItem[]> {
  try {
    return await request<SchedulerJobItem[]>("/scheduler/jobs");
  } catch {
    return [
      { job_name: "weekly_growth_review", cron_expr: "0 9 * * 1", status: "active", job_type: "review" },
      { job_name: "weekly_resource_push", cron_expr: "0 10 * * 3", status: "active", job_type: "resource_push" }
    ];
  }
}
