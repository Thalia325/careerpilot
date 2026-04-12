import { demoJobTemplates, demoMatching, demoPath, demoReportMarkdown, demoStudentProfile, type JobDetail } from "./demo-data";
export type { JobDetail };

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

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

export type StudentSession = {
  student_id: number | null;
  user_id: number;
  major: string;
  grade: string;
  career_goal: string;
  suggested_job_code: string | null;
  suggested_job_title: string | null;
};

export class APIError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public isNetworkError: boolean = false
  ) {
    super(message);
    this.name = "APIError";
  }
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
    const headers: Record<string, string> = {
      ...getAuthHeaders(),
      ...(init?.headers as Record<string, string> || {}),
    };
    if (!isFormData) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      cache: "no-store",
      headers,
    });

    if (!response.ok) {
      let detail = `请求失败 (${response.status})`;
      try {
        const body = await response.json();
        if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        else if (body.message) detail = body.message;
      } catch {}
      console.error(`[API Error] ${path}:`, detail);
      throw new APIError(response.status, detail, false);
    }

    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    const networkError = new APIError(
      0,
      `Network error: ${error instanceof Error ? error.message : "Unknown error"}`,
      true
    );
    console.error(`[Network Error] ${path}:`, networkError.message);
    throw networkError;
  }
}

export async function getStudentSession(): Promise<StudentSession> {
  return request<StudentSession>("/students/me");
}

export async function getStudentProfile(studentId: number): Promise<StudentProfile> {
  try {
    return await request<StudentProfile>(`/student-profiles/${studentId}`);
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for student profile due to network error");
      return demoStudentProfile;
    }
    throw error;
  }
}

export async function getMatching(studentId: number, jobCode: string): Promise<MatchingResult> {
  try {
    return await request<MatchingResult>("/matching/analyze", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, job_code: jobCode })
    });
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for matching due to network error");
      return demoMatching;
    }
    throw error;
  }
}

export async function getPathPlan(studentId: number, jobCode: string): Promise<PathPlan> {
  try {
    const response = await request<{ data: PathPlan }>("/career-paths/plan", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, job_code: jobCode })
    });
    return response.data;
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for path plan due to network error");
      return demoPath;
    }
    throw error;
  }
}

export async function getJobTemplates(): Promise<JobDetail[]> {
  try {
    const response = await request<{ data: JobDetail[] }>("/jobs/profiles/templates");
    return response.data;
  } catch (error) {
    console.warn("[Fallback] Using demo data for job templates:", error instanceof Error ? error.message : error);
    if (process.env.NODE_ENV === "development") {
      return demoJobTemplates;
    }
    throw error;
  }
}

export async function generateReport(studentId: number, jobCode: string): Promise<ReportDraft> {
  try {
    return await request<ReportDraft>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, job_code: jobCode })
    });
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for report due to network error");
      return {
        report_id: 1,
        student_id: studentId,
        job_code: jobCode,
        markdown_content: demoReportMarkdown,
        content: {},
        status: "draft"
      };
    }
    throw error;
  }
}

export async function parseOCR(uploadedFileId: number, documentType: string = "resume"): Promise<{ raw_text: string; layout_blocks: unknown[]; structured_json: Record<string, unknown> }> {
  return request("/ocr/parse", {
    method: "POST",
    body: JSON.stringify({ uploaded_file_id: uploadedFileId, document_type: documentType })
  });
}

export async function generateStudentProfile(studentId: number, uploadedFileIds: number[]): Promise<StudentProfile> {
  return request<StudentProfile>("/student-profiles/generate", {
    method: "POST",
    body: JSON.stringify({ student_id: studentId, uploaded_file_ids: uploadedFileIds, manual_input: null })
  });
}

export type ProfileVersionItem = {
  id: number;
  version_no: number;
  source_files: string;
  snapshot: StudentProfile;
  created_at: string;
};

export async function getProfileVersions(studentId: number): Promise<ProfileVersionItem[]> {
  const res = await request<{ items: ProfileVersionItem[] }>(`/student-profiles/${studentId}/versions`);
  return res.items;
}

function generateDemoChatReply(message: string): string {
  const keywords = ["技能", "职业", "岗位", "方向", "入行", "前景"];
  if (keywords.some((kw) => message.includes(kw))) {
    return `根据你的描述，我为你分析如下：

1. **职业方向建议**：建议关注互联网产品、数据分析等数字化岗位方向，这些领域对复合型人才需求旺盛。
2. **核心技能**：重点提升数据分析、项目管理和跨部门沟通能力。
3. **行动建议**：
   - 短期：梳理已有项目经验，提炼可量化的成果
   - 中期：寻找实习机会，积累行业认知
   - 长期：考取相关职业证书，提升竞争力

你可以上传简历让我做更精准的分析，也可以继续提问其他职业方向的问题。`;
  }
  return `你好！我是职航智策 AI 助手，专门帮助大学生进行职业规划。

你可以问我：
- 某个岗位需要什么技能？
- 如何从当前专业转入某个职业方向？
- 某个行业的发展前景如何？

请描述你的问题，我会尽力为你解答！`;
}

export async function sendChatMessage(message: string): Promise<{ reply: string }> {
  try {
    return await request<{ reply: string }>("/chat", {
      method: "POST",
      body: JSON.stringify({ message })
    });
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo reply for chat due to error:", error instanceof Error ? error.message : error);
      return { reply: generateDemoChatReply(message) };
    }
    throw error;
  }
}

export async function getSchedulerJobs(): Promise<SchedulerJobItem[]> {
  try {
    return await request<SchedulerJobItem[]>("/scheduler/jobs");
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for scheduler jobs due to network error");
      return [
        { job_name: "weekly_growth_review", cron_expr: "0 9 * * 1", status: "active", job_type: "review" },
        { job_name: "weekly_resource_push", cron_expr: "0 10 * * 3", status: "active", job_type: "resource_push" }
      ];
    }
    throw error;
  }
}

export type UploadedFileInfo = {
  id: number;
  file_name: string;
  file_type: string;
  content_type: string;
  created_at: string | null;
};

export async function listFiles(): Promise<UploadedFileInfo[]> {
  const res = await request<{ data: UploadedFileInfo[] }>("/files");
  return res.data ?? [];
}

export async function uploadFile(file: File, ownerId: number, fileType: string): Promise<{ id: number; file_name: string; url: string }> {
  const form = new FormData();
  form.append("upload", file);
  form.append("owner_id", String(ownerId));
  form.append("file_type", fileType);
  const res = await request<{ data: { id: number; file_name: string; url: string } }>("/files/upload", {
    method: "POST",
    body: form,
  });
  return res.data;
}

export async function deleteFile(fileId: number): Promise<void> {
  await request(`/files/${fileId}`, { method: "DELETE" });
}

export type AdminUser = {
  id: number;
  username: string;
  full_name: string;
  role: string;
  email: string;
  created_at: string | null;
  updated_at: string | null;
};

export async function getAdminUsers(): Promise<{ total: number; items: AdminUser[] }> {
  const res = await request<{ data: { total: number; items: AdminUser[] } }>("/admin/users");
  return res.data;
}

export type AdminStatsOverview = {
  total_users: number;
  total_jobs: number;
  total_reports: number;
  avg_match_score: number;
};

export async function getAdminStatsOverview(): Promise<AdminStatsOverview> {
  const res = await request<{ data: AdminStatsOverview }>("/admin/stats/overview");
  return res.data;
}

export type TrendDataPoint = {
  date: string;
  reports: number;
  users: number;
};

export async function getAdminStatsTrends(days: number = 14): Promise<TrendDataPoint[]> {
  const res = await request<{ data: TrendDataPoint[] }>(`/admin/stats/trends?days=${days}`);
  return res.data;
}

export type WeeklyDataPoint = {
  week: string;
  reports: number;
  matches: number;
};

export async function getAdminStatsWeekly(weeks: number = 8): Promise<WeeklyDataPoint[]> {
  const res = await request<{ data: WeeklyDataPoint[] }>(`/admin/stats/weekly?weeks=${weeks}`);
  return res.data;
}

export type SystemHealth = {
  status: string;
  database: string;
  api_response_ms: number;
  last_check: string;
  version: string;
};

export async function getSystemHealth(): Promise<SystemHealth> {
  const res = await request<{ data: SystemHealth }>("/admin/system/health");
  return res.data;
}

export type TeacherStudentReport = {
  student_id: number;
  name: string;
  target_job: string;
  match_score: number;
  report_status: string;
  major: string;
  grade: string;
  career_goal: string;
};

export async function getTeacherStudentReports(): Promise<TeacherStudentReport[]> {
  const res = await request<{ data: TeacherStudentReport[] }>("/teacher/students/reports");
  return res.data;
}

export type DistributionItem = {
  name: string;
  count: number;
};

export async function getMatchDistribution(): Promise<DistributionItem[]> {
  const res = await request<{ data: DistributionItem[] }>("/teacher/stats/match-distribution");
  return res.data;
}

export type MajorDistributionItem = {
  name: string;
  value: number;
};

export async function getMajorDistribution(): Promise<MajorDistributionItem[]> {
  const res = await request<{ data: MajorDistributionItem[] }>("/teacher/stats/major-distribution");
  return res.data;
}

export type TeacherAdviceItem = {
  student_id: number;
  name: string;
  target_job: string;
  match_score: number;
  advice: string;
};

export async function getTeacherAdvice(): Promise<TeacherAdviceItem[]> {
  const res = await request<{ data: TeacherAdviceItem[] }>("/teacher/advice");
  return res.data;
}

export type RecommendedJob = {
  job_code: string;
  title: string;
  company: string;
  salary: string;
  tags: string[];
  match_score: number | null;
};

export async function getRecommendedJobs(): Promise<RecommendedJob[]> {
  const res = await request<{ items: RecommendedJob[] }>("/students/me/recommended-jobs");
  return res.items;
}

export type HistoryItem = {
  id: string;
  type: string;
  ref_id: number;
  title: string;
  desc: string;
  time: string;
};

export async function getStudentHistory(): Promise<HistoryItem[]> {
  const res = await request<{ items: HistoryItem[] }>("/students/me/history");
  return res.items;
}

export async function renameHistoryItem(recordType: string, refId: number, customTitle: string): Promise<void> {
  await request("/students/me/history/rename", {
    method: "PATCH",
    body: JSON.stringify({ record_type: recordType, ref_id: refId, custom_title: customTitle }),
  });
}

export type JobListItem = {
  job_code: string;
  title: string;
  skills: string[];
  weights: Record<string, number>;
};

export async function getJobsList(skip: number = 0, limit: number = 100): Promise<{ total: number; items: JobListItem[] }> {
  const res = await request<{ data: { total: number; items: JobListItem[]; pagination: { total: number } } }>(`/jobs?skip=${skip}&limit=${limit}`);
  return { total: res.data.pagination?.total ?? res.data.total ?? 0, items: res.data.items };
}
