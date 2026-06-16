import type { AnalysisResult } from "../types/analysis";

export interface AnalyzeResponse {
  taskId: string;
  result: AnalysisResult;
}

export class ApiError extends Error {
  detail: unknown;

  constructor(message: string, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.detail = detail;
  }
}

export async function analyzeDemo(params: {
  demo: File;
  steam64: string;
  mapName?: string;
  windowSeconds?: number;
}): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("demo", params.demo);
  form.append("steam64", params.steam64);
  form.append("map_name", params.mapName ?? "de_dust2");
  form.append("window_seconds", String(params.windowSeconds ?? 30));

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: form
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail ?? payload;
    const message =
      typeof detail === "object" && detail && "message" in detail
        ? String((detail as { message: unknown }).message)
        : "Analysis failed";
    throw new ApiError(message, detail);
  }
  return payload as AnalyzeResponse;
}
