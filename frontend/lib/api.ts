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
  path_recommendation_id: number | null;
  profile_version_id: number | null;
  match_result_id: number | null;
  analysis_run_id: number | null;
};

export type StudentSession = {
  student_id: number | null;
  user_id: number;
  username: string;
  full_name: string;
  email: string;
  major: string;
  grade: string;
  career_goal: string;
  target_job_code: string;
  target_job_title: string;
  suggested_job_code: string | null;
  suggested_job_title: string | null;
  resolved_job_code: string;
  resolved_job_title: string;
  teacher: {
    teacher_id: number;
    teacher_user_id: number;
    teacher_name: string;
    teacher_username: string;
    teacher_email: string;
    link_id: number;
    source: string;
  } | null;
};

export type StudentInfoInput = {
  full_name: string;
  email: string;
  major: string;
  grade: string;
  career_goal: string;
  teacher_code?: string;
};

export class APIError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public isNetworkError: boolean = false,
    public errorCode?: string,
    public retryable?: boolean,
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
      let errorCode: string | undefined;
      let retryable: boolean | undefined;
      try {
        const body = await response.json();
        if (body.detail) {
          if (typeof body.detail === "object" && body.detail !== null) {
            detail = body.detail.message || JSON.stringify(body.detail);
            errorCode = body.detail.error_code;
            retryable = body.detail.retryable;
          } else {
            detail = body.detail;
          }
        } else if (body.message) {
          detail = body.message;
        }
        if (body.error_code && !errorCode) errorCode = body.error_code;
        if (body.retryable !== undefined && retryable === undefined) retryable = body.retryable;
      } catch {}
      console.error(`[API Error] ${path}:`, detail);
      throw new APIError(response.status, detail, false, errorCode, retryable);
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

export async function updateStudentInfo(data: StudentInfoInput): Promise<StudentSession> {
  return request<StudentSession>("/students/me", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function updateTargetJob(jobCode: string, jobTitle: string): Promise<{ ok: boolean; target_job_code: string; target_job_title: string; analysis_run_id: number | null }> {
  return request("/students/me/target-job", {
    method: "PUT",
    body: JSON.stringify({ job_code: jobCode, job_title: jobTitle }),
  });
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

export async function getMatching(studentId: number, jobCode: string, profileVersionId?: number | null, analysisRunId?: number | null): Promise<MatchingResult> {
  try {
    return await request<MatchingResult>("/matching/analyze", {
      method: "POST",
      body: JSON.stringify({
        student_id: studentId,
        job_code: jobCode,
        profile_version_id: profileVersionId ?? null,
        analysis_run_id: analysisRunId ?? null,
      })
    });
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for matching due to network error");
      return demoMatching;
    }
    throw error;
  }
}

export async function getMatchResult(matchId: number): Promise<MatchingResult> {
  return await request<MatchingResult>(`/matching/${matchId}`);
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

export async function getPathResult(pathId: number): Promise<PathPlan> {
  const response = await request<{ data: PathPlan }>(`/career-paths/${pathId}`);
  return response.data;
}

export async function getJobTemplates(): Promise<JobDetail[]> {
  try {
    const response = await request<{ data: JobDetail[] }>("/jobs/profiles/templates");
    return response.data;
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError && process.env.NODE_ENV === "development") {
      console.warn("[Fallback] Using demo data for job templates due to network error");
      return demoJobTemplates;
    }
    console.error("[getJobTemplates] Failed to load job templates:", error instanceof Error ? error.message : error);
    throw error;
  }
}

export type JobExploreItem = Omit<JobDetail, "category"> & {
  job_code?: string;
  category: string;
  industry?: string;
  location?: string;
  company_name?: string;
  company_size?: string;
  ownership_type?: string;
  company_intro?: string;
  source?: string;
};

export async function getJobExplorationJobs(limit: number = 180): Promise<JobExploreItem[]> {
  try {
    const response = await request<{ data: JobExploreItem[] }>(`/jobs/explore?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.warn("[Fallback] Using job templates for exploration:", error instanceof Error ? error.message : error);
    if (process.env.NODE_ENV === "development") {
      return demoJobTemplates.map((job) => ({ ...job }));
    }
    throw error;
  }
}

export async function generateReport(
  studentId: number,
  jobCode: string,
  context?: { analysis_run_id?: number | null; profile_version_id?: number | null; match_result_id?: number | null },
): Promise<ReportDraft> {
  try {
    return await request<ReportDraft>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({
        student_id: studentId,
        job_code: jobCode,
        analysis_run_id: context?.analysis_run_id ?? null,
        profile_version_id: context?.profile_version_id ?? null,
        match_result_id: context?.match_result_id ?? null,
      })
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
        status: "draft",
        path_recommendation_id: null,
        profile_version_id: null,
        match_result_id: null,
        analysis_run_id: null,
      };
    }
    throw error;
  }
}

export async function getReport(reportId: number): Promise<ReportDraft> {
  return request<ReportDraft>(`/reports/${reportId}`);
}

export async function getLatestReport(): Promise<ReportDraft> {
  return request<ReportDraft>("/reports/latest");
}

export type ReportCheckResult = {
  report_id: number;
  is_complete: boolean;
  missing_sections: string[];
  suggestions: string[];
};

export type ReportExportResult = {
  report_id: number;
  exported: {
    format: string;
    path: string;
    file_name: string;
  };
};

export async function polishReport(reportId: number, markdownContent: string): Promise<ReportDraft> {
  return request<ReportDraft>("/reports/polish", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, markdown_content: markdownContent }),
  });
}

export async function saveReport(reportId: number, markdownContent: string): Promise<{ report_id: number; status: string; markdown_content: string }> {
  return request("/reports/save", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, markdown_content: markdownContent }),
  });
}

export async function checkReport(reportId: number): Promise<ReportCheckResult> {
  return request<ReportCheckResult>("/reports/check", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId }),
  });
}

export async function exportReport(reportId: number, format: "pdf" | "docx"): Promise<ReportExportResult> {
  return request<ReportExportResult>("/reports/export", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, format }),
  });
}

export async function parseOCR(uploadedFileId: number, documentType: string = "resume"): Promise<{ raw_text: string; layout_blocks: unknown[]; structured_json: Record<string, unknown> }> {
  return request("/ocr/parse", {
    method: "POST",
    body: JSON.stringify({ uploaded_file_id: uploadedFileId, document_type: documentType })
  });
}

export async function generateStudentProfile(studentId: number, uploadedFileIds: number[], mode: "current_resume" | "merged_materials" = "current_resume"): Promise<StudentProfile> {
  return request<StudentProfile>("/student-profiles/generate", {
    method: "POST",
    body: JSON.stringify({ student_id: studentId, uploaded_file_ids: uploadedFileIds, mode, manual_input: null })
  });
}

export type ProfileVersionItem = {
  id: number;
  version_no: number;
  uploaded_file_ids: number[];
  file_summaries: { file_id: number; file_name: string; file_type: string; summary: string }[];
  source_files: string;
  snapshot: StudentProfile;
  evidence_snapshot: { source: string; excerpt: string; confidence: number }[];
  created_at: string;
};

export async function getProfileVersions(studentId: number): Promise<ProfileVersionItem[]> {
  const res = await request<{ items: ProfileVersionItem[] }>(`/student-profiles/${studentId}/versions`);
  return res.items;
}

export async function getProfileVersionDetail(studentId: number, versionId: number): Promise<ProfileVersionItem> {
  return request<ProfileVersionItem>(`/student-profiles/${studentId}/versions/${versionId}`);
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
    if (process.env.NODE_ENV === "development" && error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo reply for chat due to error:", error instanceof Error ? error.message : error);
      return { reply: generateDemoChatReply(message) };
    }
    throw error;
  }
}

export async function getGreeting(): Promise<{ greeting: string; subline: string }> {
  try {
    return await request<{ greeting: string; subline: string }>("/chat/greeting");
  } catch {
    return { greeting: "你好，想了解什么职业方向？", subline: "输入你感兴趣的岗位方向或上传简历，AI 帮你分析" };
  }
}

export async function registerAccount(
  username: string,
  password: string,
  full_name: string,
  role: string,
  email: string = "",
  teacher_code: string = "",
): Promise<{ access_token: string; role: string; user_id: number; username: string; full_name: string }> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, full_name, role, email, teacher_code }),
  });
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
  const res = await request<{ data: UploadedFileInfo[] }>("/files/");
  return res.data ?? [];
}

export async function uploadFile(file: File, ownerId: number, fileType: string): Promise<{ id: number; file_name: string; file_type: string; created_at: string | null; url: string }> {
  const form = new FormData();
  form.append("upload", file);
  form.append("owner_id", String(ownerId));
  form.append("file_type", fileType);
  const res = await request<{ data: { id: number; file_name: string; file_type: string; created_at: string | null; url: string } }>("/files/upload", {
    method: "POST",
    body: form,
  });
  return res.data;
}

export async function deleteFile(fileId: number): Promise<void> {
  await request(`/files/${fileId}`, { method: "DELETE" });
}

export async function clearFiles(): Promise<void> {
  await request("/files/clear", { method: "DELETE" });
}

export type AdminUser = {
  id: number;
  username: string;
  full_name: string;
  role: string;
  email: string;
  created_at: string | null;
  updated_at: string | null;
  profile?: {
    student_id?: number;
    major?: string;
    grade?: string;
    career_goal?: string;
    target_job_code?: string;
    learning_preferences?: Record<string, unknown>;
    teacher_id?: number;
    department?: string;
    title?: string;
  };
};

export type AdminUserInput = {
  username: string;
  password?: string;
  full_name: string;
  role: "student" | "teacher" | "admin";
  email: string;
};

export async function getAdminUsers(params?: { keyword?: string; role?: string; skip?: number; limit?: number }): Promise<{ total: number; items: AdminUser[] }> {
  const qs = new URLSearchParams();
  if (params?.keyword) qs.set("keyword", params.keyword);
  if (params?.role) qs.set("role", params.role);
  if (params?.skip) qs.set("skip", String(params.skip));
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  const path = `/admin/users${query ? `?${query}` : ""}`;
  const res = await request<{ data: { total: number; items: AdminUser[] } }>(path);
  return res.data;
}

export async function getAdminUser(userId: number): Promise<AdminUser> {
  const res = await request<{ data: AdminUser }>(`/admin/users/${userId}`);
  return res.data;
}

export async function createAdminUser(data: AdminUserInput & { password: string }): Promise<AdminUser> {
  const res = await request<{ data: AdminUser }>("/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return res.data;
}

export async function updateAdminUser(userId: number, data: Partial<AdminUserInput>): Promise<AdminUser> {
  const res = await request<{ data: AdminUser }>(`/admin/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.data;
}

export async function deleteAdminUser(userId: number): Promise<void> {
  await request(`/admin/users/${userId}`, { method: "DELETE" });
}

// --- Admin Position (JobProfile) CRUD ---

export type AdminPosition = {
  id: number;
  job_code: string;
  title: string;
  summary: string;
  skill_requirements: string[];
  certificate_requirements: string[];
  innovation_requirements: string;
  learning_requirements: string;
  resilience_requirements: string;
  communication_requirements: string;
  internship_requirements: string;
  capability_scores: Record<string, number>;
  dimension_weights: Record<string, number>;
  explanation_json: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
};

export type AdminPositionInput = {
  job_code: string;
  title: string;
  summary?: string;
  skill_requirements?: string[];
  certificate_requirements?: string[];
  innovation_requirements?: string;
  learning_requirements?: string;
  resilience_requirements?: string;
  communication_requirements?: string;
  internship_requirements?: string;
  capability_scores?: Record<string, number>;
  dimension_weights?: Record<string, number>;
  explanation_json?: Record<string, unknown>;
};

export async function getAdminPositions(params: { keyword?: string; skip?: number; limit?: number } = {}): Promise<{ total: number; items: AdminPosition[] }> {
  const qs = new URLSearchParams();
  if (params.keyword) qs.set("keyword", params.keyword);
  if (params.skip !== undefined) qs.set("skip", String(params.skip));
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  const query = qs.toString();
  const path = `/admin/positions${query ? `?${query}` : ""}`;
  const res = await request<{ data: { total: number; items: AdminPosition[] } }>(path);
  return res.data;
}

export async function getAdminPosition(positionId: number): Promise<AdminPosition> {
  const res = await request<{ data: AdminPosition }>(`/admin/positions/${positionId}`);
  return res.data;
}

export async function createAdminPosition(data: AdminPositionInput): Promise<AdminPosition> {
  const res = await request<{ data: AdminPosition }>("/admin/positions", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return res.data;
}

export async function updateAdminPosition(positionId: number, data: Partial<AdminPositionInput>): Promise<AdminPosition> {
  const res = await request<{ data: AdminPosition }>(`/admin/positions/${positionId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.data;
}

export async function deleteAdminPosition(positionId: number): Promise<void> {
  await request(`/admin/positions/${positionId}`, { method: "DELETE" });
}

export type AdminStatsOverview = {
  total_users: number;
  total_positions: number;
  total_reports: number;
  total_matches: number;
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
  last_analysis_time: string | null;
  followup_status: string;
};

export type TeacherReportFilters = {
  major?: string;
  grade?: string;
  target_job?: string;
  report_status?: string;
  score_min?: number;
  score_max?: number;
};

export async function getTeacherStudentReports(filters?: TeacherReportFilters): Promise<TeacherStudentReport[]> {
  const params = new URLSearchParams();
  if (filters?.major) params.set("major", filters.major);
  if (filters?.grade) params.set("grade", filters.grade);
  if (filters?.target_job) params.set("target_job", filters.target_job);
  if (filters?.report_status) params.set("report_status", filters.report_status);
  if (filters?.score_min !== undefined) params.set("score_min", String(filters.score_min));
  if (filters?.score_max !== undefined) params.set("score_max", String(filters.score_max));
  const query = params.toString() ? `?${params.toString()}` : "";
  const res = await request<{ data: TeacherStudentReport[] }>(`/teacher/students/reports${query}`);
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

export type TeacherOverviewStats = {
  total_students: number;
  students_with_resume: number;
  students_with_profile: number;
  students_with_report: number;
  avg_match_score: number;
  pending_review_reports: number;
  students_need_followup: number;
};

export async function getTeacherOverviewStats(): Promise<TeacherOverviewStats> {
  const res = await request<{ data: TeacherOverviewStats }>("/teacher/stats/overview");
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

export type TeacherInfo = {
  teacher_id: number;
  user_id: number;
  username: string;
  full_name: string;
  email: string;
  department: string;
  title: string;
  student_count: number;
};

export type TeacherInfoInput = {
  full_name: string;
  email: string;
  department: string;
  title: string;
};

export async function getTeacherInfo(): Promise<TeacherInfo> {
  const res = await request<{ data: TeacherInfo }>("/teacher/me");
  return res.data;
}

export async function updateTeacherInfo(data: TeacherInfoInput): Promise<TeacherInfo> {
  const res = await request<{ data: TeacherInfo }>("/teacher/me", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.data;
}

export type TeacherStudentReportListItem = {
  report_id: number;
  target_job: string;
  status: string;
  profile_version_id: number | null;
  match_result_id: number | null;
  analysis_run_id: number | null;
  created_at: string | null;
  updated_at: string | null;
  profile_version_no: number | null;
};

export async function getTeacherStudentReportList(studentId: number): Promise<TeacherStudentReportListItem[]> {
  const res = await request<{ data: TeacherStudentReportListItem[] }>(`/teacher/students/${studentId}/reports`);
  return res.data;
}

export type TeacherReportDetail = {
  report_id: number;
  student_id: number;
  student_name: string;
  student_major: string;
  student_grade: string;
  target_job_code: string;
  status: string;
  content: Record<string, unknown>;
  markdown_content: string;
  resume_summary: Record<string, unknown>;
  profile_snapshot: Record<string, unknown>;
  match_analysis: {
    total_score: number;
    gaps: { item: string; description: string }[];
    strengths: string[];
    suggestions: string[];
  };
  profile_version_id: number | null;
  match_result_id: number | null;
  path_recommendation_id: number | null;
  analysis_run_id: number | null;
  created_at: string | null;
  updated_at: string | null;
};

export async function getTeacherReportDetail(reportId: number): Promise<TeacherReportDetail> {
  const res = await request<{ data: TeacherReportDetail }>(`/teacher/reports/${reportId}`);
  return res.data;
}

export type ClassOverviewData = {
  job_distribution: { name: string; value: number }[];
  report_completion_rate: number;
  resume_completeness: { name: string; value: number }[];
  skill_gaps: { name: string; count: number }[];
  followup_students: { student_id: number; name: string; major: string; career_goal: string }[];
};

export async function getClassOverview(): Promise<ClassOverviewData> {
  const res = await request<{ data: ClassOverviewData }>("/teacher/stats/class-overview");
  return res.data;
}

export async function updateFollowupStatus(
  studentId: number,
  data: { status?: string; next_followup_date?: string; teacher_notes?: string },
): Promise<{ student_id: number; status: string; deadline: string | null; updated: boolean }> {
  const params = new URLSearchParams();
  if (data.status) params.set("status_value", data.status);
  if (data.next_followup_date) params.set("next_followup_date", data.next_followup_date);
  if (data.teacher_notes) params.set("teacher_notes", data.teacher_notes);
  const res = await request<{ data: { student_id: number; status: string; deadline: string | null; updated: boolean } }>(
    `/teacher/students/${studentId}/followup?${params.toString()}`,
    { method: "PATCH" },
  );
  return res.data;
}

// --- Teacher Comment CRUD ---

export type TeacherCommentItem = {
  id: number;
  teacher_id: number;
  teacher_name: string;
  student_id: number;
  report_id: number;
  comment: string;
  priority: string;
  visible_to_student: boolean;
  student_read_at: string | null;
  follow_up_status: string | null;
  next_follow_up_date: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export async function createTeacherComment(
  reportId: number,
  commentText: string,
  options: { priority?: string; visible_to_student?: boolean; follow_up_status?: string; next_follow_up_date?: string } = {},
): Promise<{ id: number; comment: string; priority: string; visible_to_student: boolean; follow_up_status: string | null; next_follow_up_date: string | null; created_at: string | null }> {
  const params = new URLSearchParams();
  params.set("comment_text", commentText);
  params.set("priority", options.priority || "normal");
  params.set("visible_to_student", String(options.visible_to_student !== false));
  if (options.follow_up_status) params.set("follow_up_status", options.follow_up_status);
  if (options.next_follow_up_date) params.set("next_follow_up_date", options.next_follow_up_date);
  const res = await request<{ data: { id: number; comment: string; priority: string; visible_to_student: boolean; follow_up_status: string | null; next_follow_up_date: string | null; created_at: string | null } }>(
    `/teacher/reports/${reportId}/comments?${params.toString()}`,
    { method: "POST" },
  );
  return res.data;
}

export async function getTeacherComments(reportId: number): Promise<TeacherCommentItem[]> {
  const res = await request<{ data: TeacherCommentItem[] }>(`/teacher/reports/${reportId}/comments`);
  return res.data;
}

export async function updateTeacherComment(
  commentId: number,
  data: { comment_text?: string; priority?: string; visible_to_student?: boolean; follow_up_status?: string; next_follow_up_date?: string },
): Promise<{ id: number; comment: string; priority: string; visible_to_student: boolean; follow_up_status: string | null; next_follow_up_date: string | null; updated_at: string | null }> {
  const params = new URLSearchParams();
  if (data.comment_text !== undefined) params.set("comment_text", data.comment_text);
  if (data.priority !== undefined) params.set("priority", data.priority);
  if (data.visible_to_student !== undefined) params.set("visible_to_student", String(data.visible_to_student));
  if (data.follow_up_status !== undefined) params.set("follow_up_status", data.follow_up_status);
  if (data.next_follow_up_date !== undefined) params.set("next_follow_up_date", data.next_follow_up_date);
  const res = await request<{ data: { id: number; comment: string; priority: string; visible_to_student: boolean; follow_up_status: string | null; next_follow_up_date: string | null; updated_at: string | null } }>(
    `/teacher/comments/${commentId}?${params.toString()}`,
    { method: "PUT" },
  );
  return res.data;
}

export async function deleteTeacherComment(commentId: number): Promise<void> {
  await request(`/teacher/comments/${commentId}`, { method: "DELETE" });
}

// --- Student: Teacher Feedback ---

export type TeacherFeedbackItem = {
  id: number;
  teacher_name: string;
  report_id: number;
  comment: string;
  priority: string;
  student_read_at: string | null;
  created_at: string | null;
};

export async function getStudentTeacherFeedback(): Promise<TeacherFeedbackItem[]> {
  const res = await request<{ items: TeacherFeedbackItem[] }>("/students/me/teacher-feedback");
  return res.items;
}

export async function markFeedbackRead(commentId: number): Promise<{ ok: boolean; read_at: string }> {
  return request(`/students/me/teacher-feedback/${commentId}/read`, { method: "POST" });
}

// --- Teacher Roster Management ---

export type RosterCandidate = {
  student_id: number;
  user_id: number;
  username: string;
  full_name: string;
  email: string;
  major: string;
  grade: string;
  already_bound: boolean;
};

export type RosterAddResult = {
  id: number;
  teacher_id: number;
  student_id: number;
  group_name: string;
  source: string;
  status: string;
  created_at: string | null;
};

export type RosterRemoveResult = {
  removed: boolean;
  student_id: number;
};

export async function searchRosterCandidates(keyword: string): Promise<RosterCandidate[]> {
  const res = await request<{ data: RosterCandidate[] }>(`/teacher/roster/search?keyword=${encodeURIComponent(keyword)}`);
  return res.data;
}

export async function addStudentToRoster(studentId: number, groupName?: string): Promise<RosterAddResult> {
  const query = groupName ? `?group_name=${encodeURIComponent(groupName)}` : "";
  return request(`/teacher/roster/${studentId}${query}`, { method: "POST" });
}

export async function removeStudentFromRoster(studentId: number): Promise<RosterRemoveResult> {
  return request(`/teacher/roster/${studentId}`, { method: "DELETE" });
}

export type RecommendedJob = {
  job_code: string;
  title: string;
  company: string;
  salary: string;
  location?: string;
  industry?: string;
  company_size?: string;
  ownership_type?: string;
  summary?: string;
  tags: string[];
  matched_tags?: string[];
  missing_tags?: string[];
  experience_tags?: string[];
  reason?: string;
  match_score: number | null;
  base_score?: number | null;
  experience_score?: number | null;
  skill_score?: number | null;
  potential_score?: number | null;
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
  profile_version_id?: number;
  uploaded_file_ids?: number[];
  analysis_run_id?: number;
  match_result_id?: number;
  source_file_id?: number;
};

export async function getStudentHistory(type?: string): Promise<HistoryItem[]> {
  const query = type ? `?type=${encodeURIComponent(type)}` : "";
  const res = await request<{ items: HistoryItem[] }>(`/students/me/history${query}`);
  return res.items;
}

export async function renameHistoryItem(recordType: string, refId: number, customTitle: string): Promise<void> {
  await request("/students/me/history/rename", {
    method: "PATCH",
    body: JSON.stringify({ record_type: recordType, ref_id: refId, custom_title: customTitle }),
  });
}

export type HistoryDetailPayload = {
  type: string;
  ref_id: number;
  [key: string]: unknown;
};

export async function getHistoryDetail(recordType: string, refId: number): Promise<HistoryDetailPayload> {
  const res = await request<HistoryDetailPayload>(
    `/students/me/history/detail?type=${encodeURIComponent(recordType)}&ref_id=${refId}`
  );
  return res;
}

export type ChatHistoryMessage = {
  id: number;
  role: string;
  content: string;
  created_at: string;
  has_context: boolean;
};

export type ChatHistoryResponse = {
  messages: ChatHistoryMessage[];
  target_message_id: number;
};

export async function getChatHistory(messageId: number): Promise<ChatHistoryResponse> {
  return await request<ChatHistoryResponse>(`/chat/history/${messageId}`);
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

// --- Analysis Pipeline State ---

export type AnalysisRunState = {
  run_id: number;
  status: "pending" | "running" | "completed" | "failed";
  current_step: string;
  failed_step: string;
  error_detail: string;
  step_results: Record<string, boolean>;
  uploaded_file_ids?: number[];
  resume_file_id?: number | null;
  profile_version_id?: number | null;
  target_job_code?: string | null;
  match_result_id?: number | null;
  path_recommendation_id?: number | null;
  report_id?: number | null;
};

export async function startAnalysisRun(studentId: number, jobCode: string, fileIds: number[]): Promise<AnalysisRunState> {
  return request<AnalysisRunState>("/analysis/start", {
    method: "POST",
    body: JSON.stringify({ student_id: studentId, job_code: jobCode, file_ids: fileIds }),
  });
}

export async function getAnalysisRun(runId: number): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}`);
}

export async function getLatestAnalysis(): Promise<AnalysisRunState> {
  return request<AnalysisRunState>("/analysis/latest");
}

export async function updateAnalysisContext(
  runId: number,
  data: {
    profile_version_id?: number | null;
    target_job_code?: string | null;
    match_result_id?: number | null;
    path_recommendation_id?: number | null;
    report_id?: number | null;
  },
): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}/context`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function markStepRunning(runId: number, stepKey: string): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}/step/${stepKey}/running`, { method: "POST" });
}

export async function markStepComplete(runId: number, stepKey: string): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}/step/${stepKey}/complete`, { method: "POST" });
}

export async function markStepFailed(runId: number, stepKey: string, errorDetail: string): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}/step/${stepKey}/fail`, {
    method: "POST",
    body: JSON.stringify({ error_detail: errorDetail }),
  });
}

export async function markAnalysisComplete(runId: number): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}/complete`, { method: "POST" });
}

export async function resetAnalysisRun(runId: number): Promise<AnalysisRunState> {
  return request<AnalysisRunState>(`/analysis/${runId}/reset`, { method: "POST" });
}

// --- Password change (US-028) ---

export async function changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
  const res = await request<{ message: string }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
  return res;
}

export async function adminResetPassword(userId: number, newPassword: string): Promise<{ message: string }> {
  const res = await request<{ message: string }>(`/admin/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify({ password: newPassword }),
  });
  return res;
}

export async function teacherResetStudentPassword(studentUserId: number, newPassword: string): Promise<{ message: string }> {
  const res = await request<{ message: string }>(`/teacher/students/${studentUserId}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
  return res;
}
