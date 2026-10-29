/**
 * Typed API Client for talking to the Python FastAPI Backend (`http://localhost:8000`).
 *
 * Mentor Note:
 * Notice how we generate and store a unique `client_id` in the browser's `localStorage`
 * and send it as the `X-Client-ID` header on every request. This keeps each user's
 * generation history and daily quota isolated without forcing a complex login flow.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type AspectRatio = "9:16" | "16:9" | "1:1";
export type DurationSeconds = 5 | 10;
export type GenerationMode = "text_to_video" | "image_to_video";
export type StylePreset =
  | "cinematic"
  | "anime"
  | "cyberpunk"
  | "3d_animation"
  | "photorealistic"
  | "vintage_film"
  | "dark_fantasy"
  | "commercial";
export type JobStatus = "queued" | "processing" | "completed" | "failed";

export interface StudioStatus {
  active_provider: string;
  is_demo_mode: boolean;
  provider_display_name: string;
  daily_limit: number;
  generations_used_today: number;
  generations_remaining_today: number;
  total_estimated_spend_today_usd: number;
  max_upload_size_mb: number;
}

export interface CostEstimate {
  provider_name: string;
  is_demo: boolean;
  duration_seconds: number;
  estimated_cost_usd: number;
  cost_explanation: string;
}

export interface VideoJob {
  id: string;
  client_id: string;
  generation_type: GenerationMode;
  prompt: string;
  enhanced_prompt?: string | null;
  style_preset: StylePreset;
  aspect_ratio: AspectRatio;
  duration_seconds: DurationSeconds;
  source_image_url?: string | null;
  provider_name: string;
  is_demo: boolean;
  estimated_cost_usd: number;
  status: JobStatus;
  progress_percent: number;
  video_url?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadImageResult {
  filename: string;
  image_url: string;
  width: number;
  height: number;
  size_kb: number;
}

export function getClientId(): string {
  if (typeof window === "undefined") return "server-render";
  const storageKey = "ai_video_studio_client_id";
  let clientId = window.localStorage.getItem(storageKey);
  if (!clientId) {
    clientId =
      "user_" +
      Math.random().toString(36).substring(2, 10) +
      "_" +
      Date.now().toString(36);
    window.localStorage.setItem(storageKey, clientId);
  }
  return clientId;
}

function getHeaders(isJson = true): HeadersInit {
  const headers: Record<string, string> = {
    "X-Client-ID": getClientId(),
  };
  if (isJson) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP Error ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail =
          typeof errJson.detail === "string"
            ? errJson.detail
            : JSON.stringify(errJson.detail);
      }
    } catch {
      // Fallback if response is not JSON
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export async function fetchStudioStatus(): Promise<StudioStatus> {
  const res = await fetch(`${API_BASE_URL}/api/videos/studio-status`, {
    headers: getHeaders(),
    cache: "no-store",
  });
  return handleResponse<StudioStatus>(res);
}

export async function fetchCostEstimate(params: {
  generation_type: GenerationMode;
  duration_seconds: DurationSeconds;
  aspect_ratio: AspectRatio;
  style_preset: StylePreset;
}): Promise<CostEstimate> {
  const res = await fetch(`${API_BASE_URL}/api/videos/estimate-cost`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  return handleResponse<CostEstimate>(res);
}

export async function enhancePrompt(params: {
  prompt: string;
  style_preset: StylePreset;
  aspect_ratio: AspectRatio;
}): Promise<{
  original_prompt: string;
  enhanced_prompt: string;
  style_preset: string;
  enhancer_source: string;
}> {
  const res = await fetch(`${API_BASE_URL}/api/prompts/enhance`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  return handleResponse(res);
}

export async function uploadReferenceImage(
  file: File
): Promise<UploadImageResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/api/videos/upload-image`, {
    method: "POST",
    headers: getHeaders(false),
    body: formData,
  });
  return handleResponse<UploadImageResult>(res);
}

export async function submitVideoGeneration(params: {
  generation_type: GenerationMode;
  prompt: string;
  style_preset: StylePreset;
  aspect_ratio: AspectRatio;
  duration_seconds: DurationSeconds;
  source_image_url?: string | null;
  confirm_paid_generation: boolean;
}): Promise<VideoJob> {
  const res = await fetch(`${API_BASE_URL}/api/videos/generate`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  return handleResponse<VideoJob>(res);
}

export async function pollVideoJob(jobId: string): Promise<VideoJob> {
  const res = await fetch(`${API_BASE_URL}/api/videos/${jobId}`, {
    headers: getHeaders(),
    cache: "no-store",
  });
  return handleResponse<VideoJob>(res);
}

export async function fetchHistory(): Promise<{
  items: VideoJob[];
  total: number;
}> {
  const res = await fetch(`${API_BASE_URL}/api/videos/history`, {
    headers: getHeaders(),
    cache: "no-store",
  });
  return handleResponse<{ items: VideoJob[]; total: number }>(res);
}

export async function deleteHistoryJob(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/videos/${jobId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) {
    throw new Error("Failed to delete history item.");
  }
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/api/videos/${jobId}/download`;
}
