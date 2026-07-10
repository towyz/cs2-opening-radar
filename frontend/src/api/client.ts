import type { AnalysisResult } from "../types/analysis";

export interface AnalyzeResponse {
  taskId: string;
  result: AnalysisResult;
}

export interface AnalyzePlayerResponse {
  taskIds: string[];
  results: AnalysisResult[];
}

export interface PlayerOption {
  name: string;
  steam64: string;
}

export interface ImportedDemo {
  id: string;
  name: string;
}

export interface ImportDemoResponse {
  demo: ImportedDemo;
  players: PlayerOption[];
}

export interface LocalDemoItem {
  path: string;
  name: string;
  size: number;
  modifiedTime: string;
  kind: string;
}

export interface LocalDemoListResponse {
  configPath: string;
  demos: LocalDemoItem[];
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

export async function importDemo(params: {
  demo: File;
  mapName?: string;
}): Promise<ImportDemoResponse> {
  const form = new FormData();
  form.append("demo", params.demo);
  form.append("map_name", params.mapName ?? "de_dust2");

  const response = await fetch("/api/import-demo", {
    method: "POST",
    body: form
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw apiErrorFromPayload(payload);
  }
  return payload as ImportDemoResponse;
}

export async function listLocalDemos(): Promise<LocalDemoListResponse> {
  const response = await fetch("/api/local-demos");
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw apiErrorFromPayload(payload);
  }
  return payload as LocalDemoListResponse;
}

export async function analyzeLocalDemo(params: {
  path: string;
  steam64: string;
  mapName?: string;
  windowSeconds?: number;
}): Promise<AnalyzeResponse> {
  const response = await fetch("/api/analyze-local", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      path: params.path,
      steam64: params.steam64,
      map_name: params.mapName ?? "de_dust2",
      window_seconds: params.windowSeconds ?? 30
    })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw apiErrorFromPayload(payload);
  }
  return payload as AnalyzeResponse;
}

export async function importLocalDemo(params: {
  path: string;
  mapName?: string;
}): Promise<ImportDemoResponse> {
  const response = await fetch("/api/import-local-demo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      path: params.path,
      map_name: params.mapName ?? "de_dust2"
    })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw apiErrorFromPayload(payload);
  }
  return payload as ImportDemoResponse;
}

export async function analyzePlayer(params: {
  demoIds: string[];
  steam64: string;
  mapName?: string;
  windowSeconds?: number;
}): Promise<AnalyzePlayerResponse> {
  const response = await fetch("/api/analyze-player", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      demo_ids: params.demoIds,
      steam64: params.steam64,
      map_name: params.mapName ?? "de_dust2",
      window_seconds: params.windowSeconds ?? 30
    })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw apiErrorFromPayload(payload);
  }
  return payload as AnalyzePlayerResponse;
}

function apiErrorFromPayload(payload: unknown): ApiError {
  const detail =
    typeof payload === "object" && payload && "detail" in payload
      ? (payload as { detail: unknown }).detail
      : payload;
  const message =
    typeof detail === "object" && detail && "message" in detail
      ? String((detail as { message: unknown }).message)
      : "Analysis failed";
  return new ApiError(message, detail);
}
