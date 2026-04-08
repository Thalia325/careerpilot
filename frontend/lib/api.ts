import { demoJobTemplates, demoMatching, demoPath, demoReportMarkdown, demoStudentProfile } from "./demo-data";

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

class APIError extends Error {
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
      const error = new APIError(
        response.status,
        `API request failed: ${response.status} ${response.statusText}`,
        false
      );
      console.error(`[API Error] ${path}:`, error.message);
      throw error;
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

export async function getStudentProfile(): Promise<StudentProfile> {
  try {
    return await request<StudentProfile>("/student-profiles/1");
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo data for student profile due to network error");
      // Only use demo data as fallback in development
      if (process.env.NODE_ENV === "development") {
        return demoStudentProfile;
      }
      throw error;
    }
    throw error;
  }
}

export async function getMatching(): Promise<MatchingResult> {
  try {
    return await request<MatchingResult>("/matching/analyze", {
      method: "POST",
      body: JSON.stringify({ student_id: 1, job_code: "J-FE-001" })
    });
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo data for matching due to network error");
      if (process.env.NODE_ENV === "development") {
        return demoMatching;
      }
      throw error;
    }
    throw error;
  }
}

export async function getPathPlan(): Promise<PathPlan> {
  try {
    const response = await request<{ data: PathPlan }>("/career-paths/plan", {
      method: "POST",
      body: JSON.stringify({ student_id: 1, job_code: "J-FE-001" })
    });
    return response.data;
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo data for path plan due to network error");
      if (process.env.NODE_ENV === "development") {
        return demoPath;
      }
      throw error;
    }
    throw error;
  }
}

export async function getJobTemplates(): Promise<Array<{ title: string }>> {
  try {
    const response = await request<{ data: Array<{ title: string }> }>("/jobs/profiles/templates");
    return response.data;
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo data for job templates due to network error");
      if (process.env.NODE_ENV === "development") {
        return demoJobTemplates.map((title) => ({ title }));
      }
      throw error;
    }
    throw error;
  }
}

export async function generateDemoReport(): Promise<ReportDraft> {
  try {
    return await request<ReportDraft>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({ student_id: 1, job_code: "J-FE-001" })
    });
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo data for report due to network error");
      if (process.env.NODE_ENV === "development") {
        return {
          report_id: 1,
          student_id: 1,
          job_code: "J-FE-001",
          markdown_content: demoReportMarkdown,
          content: {},
          status: "draft"
        };
      }
      throw error;
    }
    throw error;
  }
}

export async function sendChatMessage(message: string): Promise<{ reply: string }> {
  return request<{ reply: string }>("/chat", {
    method: "POST",
    body: JSON.stringify({ message })
  });
}

export type ApiKeyStatus = {
  configured: boolean;
  auth_mode?: string | null;
  api_key_masked?: string | null;
  secret_key_masked?: string | null;
  model_name?: string | null;
};

export async function getApiKeyStatus(): Promise<ApiKeyStatus> {
  return request<ApiKeyStatus>("/api-key");
}

export async function saveApiKey(params: {
  api_key: string;
  secret_key?: string;
  auth_mode: string;
}): Promise<ApiKeyStatus> {
  return request<ApiKeyStatus>("/api-key", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function deleteApiKey(): Promise<ApiKeyStatus> {
  return request<ApiKeyStatus>("/api-key", {
    method: "DELETE"
  });
}

export async function testApiKey(): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>("/api-key/test", {
    method: "POST"
  });
}

export async function getSchedulerJobs(): Promise<SchedulerJobItem[]> {
  try {
    return await request<SchedulerJobItem[]>("/scheduler/jobs");
  } catch (error) {
    if (error instanceof APIError && error.isNetworkError) {
      console.warn("[Fallback] Using demo data for scheduler jobs due to network error");
      if (process.env.NODE_ENV === "development") {
        return [
          { job_name: "weekly_growth_review", cron_expr: "0 9 * * 1", status: "active", job_type: "review" },
          { job_name: "weekly_resource_push", cron_expr: "0 10 * * 3", status: "active", job_type: "resource_push" }
        ];
      }
      throw error;
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
