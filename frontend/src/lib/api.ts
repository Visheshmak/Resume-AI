export type DashboardOverview = { resume_count: number; job_count: number; analysis_count: number; completed_analysis_count: number };
export type User = { id: string; email: string; full_name: string; created_at: string };
export type Resume = { id: string; title: string; original_filename: string; file_type: string; size_bytes: number; status: string; created_at: string };
export type ResumeDetail = Resume & { extraction: ResumeExtraction | null; extracted_text: string | null };
export type ResumeExtraction = { candidate?: { name?: { value: string } | null }; contact?: Record<string, unknown>; skills?: Record<string, Skill[]>; experience?: Experience[]; projects?: Project[]; quality_signals?: QualitySignal[]; bullet_analysis?: BulletAnalysis[]; document_signals?: { page_count: number; line_count: number; layout: string } };
export type Skill = { name: string; category: string; aliases_detected: string[]; evidence: Evidence[] };
export type Evidence = { id: string; kind?: string; source_id?: string; excerpt?: string; text?: string; confidence?: number; section?: string; line_number?: number };
export type Experience = { company?: string | null; role?: string | null; responsibilities: string[]; technologies: string[]; evidence: Evidence[] };
export type Project = { name?: string | null; description?: string | null; technologies: string[]; evidence: Evidence[] };
export type QualitySignal = { code: string; severity: string; message: string; evidence: Evidence[] };
export type BulletAnalysis = { text: string; weak: boolean; recommendation?: string | null; has_metric: boolean; evidence: Evidence[] };
export type Job = { id: string; title: string; raw_text: string; structured_data: JobExtraction; created_at: string };
export type JobExtraction = { required_skills: string[]; preferred_skills: string[]; responsibilities: string[]; keywords: string[]; experience_requirements: string[]; education_requirements: string[]; requirements: Requirement[] };
export type Requirement = { id: string; text: string; requirement_type: string; skill?: string | null; evidence: Evidence[] };
export type Analysis = { id: string; resume_id: string; job_description_id: string; status: string; score_summary: JobFitReport; created_at: string; completed_at?: string | null; error_message?: string | null };
export type AnalysisJob = { job_id: string; analysis_id: string; status: "queued" | "processing" | "completed" | "retrying" | "failed" | "permanently_failed"; progress: number; current_step: string; attempts: number; error_message?: string | null; created_at: string; started_at?: string | null; completed_at?: string | null };
export type Score = { category: string; score: number; reason: string; matched: number; total: number };
export type Match = { skill: string; status: "matched" | "partial" | "missing" | "concept_match"; requirement_type: string; resume_evidence: Evidence[]; jd_evidence: Evidence[]; confidence: number; explanation: string };
export type JobFitReport = { overall_match: number; scores: Score[]; keyword_matches: Match[]; matched_skills: Match[]; missing_skills: Match[]; partial_matches: Match[]; strong_evidence: Match[]; weak_evidence: Match[]; recommended_improvements: string[]; priority_improvements: { priority: string; recommendation: string }[]; explanation: string };
export type InterviewQuestion = { question: string; category: string; difficulty: string; why_relevant: string; evidence_ids: string[]; confidence: number };

export type ApiState<T> = { data: T | null; loading: boolean; error: string | null };

const TOKEN_KEY = "resumeiq.access_token";

export function getToken() { return localStorage.getItem(TOKEN_KEY); }
export function setToken(token: string) { localStorage.setItem(TOKEN_KEY, token); }
export function clearToken() { localStorage.removeItem(TOKEN_KEY); }

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let detail = "Request failed";
    try { detail = (await response.json()).detail ?? detail; } catch { /* preserve safe fallback */ }
    throw new Error(response.status === 401 ? "Your session has expired. Sign in again." : detail);
  }
  return response.json() as Promise<T>;
}

export async function register(email: string, full_name: string, password: string) { return request<User>("/api/v1/auth/register", { method: "POST", body: JSON.stringify({ email, full_name, password }) }); }
export async function login(email: string, password: string) { const result = await request<{ access_token: string }>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); setToken(result.access_token); return request<User>("/api/v1/auth/me"); }
export async function logout() { try { await request("/api/v1/auth/logout", { method: "POST" }); } finally { clearToken(); } }
export async function getMe() { return request<User>("/api/v1/auth/me"); }

export function uploadResume(file: File, title: string, onProgress: (value: number) => void): Promise<Resume> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/resumes/upload");
    const token = getToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.upload.onprogress = (event) => { if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100)); };
    xhr.onerror = () => reject(new Error("Network failure while uploading the resume."));
    xhr.onload = () => { try { const body = JSON.parse(xhr.responseText); if (xhr.status >= 200 && xhr.status < 300) resolve(body); else reject(new Error(body.detail ?? "Resume upload failed.")); } catch { reject(new Error("The server returned an unreadable response.")); } };
    const body = new FormData(); body.append("file", file); body.append("title", title || file.name); xhr.send(body);
  });
}
export async function getResume(id: string) { return request<ResumeDetail>(`/api/v1/resumes/${id}`); }
export async function createJob(title: string, raw_text: string) { return request<Job>("/api/v1/jobs", { method: "POST", body: JSON.stringify({ title, raw_text }) }); }
export async function createAnalysis(resume_id: string, job_description_id: string) { return request<Analysis & { job_id: string }>("/api/v1/analysis", { method: "POST", body: JSON.stringify({ resume_id, job_description_id }) }); }
export async function getAnalysisJob(jobId: string) { return request<AnalysisJob>(`/api/v1/analysis/jobs/${jobId}`); }
export async function waitForAnalysis(jobId: string, onUpdate: (job: AnalysisJob) => void) {
  for (;;) {
    const job = await getAnalysisJob(jobId);
    onUpdate(job);
    if (job.status === "completed") return getAnalysis(job.analysis_id);
    if (job.status === "failed" || job.status === "permanently_failed") throw new Error(job.error_message || "Analysis processing failed.");
    await new Promise((resolve) => window.setTimeout(resolve, 900));
  }
}
export async function getAnalysis(id: string) { return request<Analysis>(`/api/v1/analysis/${id}`); }
export async function getAnalysisEvidence(id: string) { return request<Evidence[]>(`/api/v1/analysis/${id}/evidence`); }
export async function generateInterviewQuestions(id: string) { return request<{ questions: InterviewQuestion[] }>(`/api/v1/analysis/${id}/interview-questions`, { method: "POST" }); }

export async function getDashboardOverview(): Promise<DashboardOverview> {
  return request<DashboardOverview>("/api/v1/dashboard/overview");
}

export async function getHealth(): Promise<boolean> {
  const response = await fetch("/health");
  return response.ok;
}
