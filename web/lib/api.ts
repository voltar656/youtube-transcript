import { TranscriptRequest, TranscriptResponse, ErrorResponse } from "./types";

function getApiUrl(): string {
  if (typeof window !== "undefined") {
    return "/api";
  }
  return process.env.BACKEND_URL || "http://localhost:8000";
}

export class ApiError extends Error {
  constructor(
    public error: string,
    public message: string,
    public videoId?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchTranscript(
  request: TranscriptRequest
): Promise<TranscriptResponse> {
  const response = await fetch(`${getApiUrl()}/transcript`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const data = await response.json();
    const detail = data.detail as ErrorResponse;
    throw new ApiError(
      detail?.error || "UnknownError",
      detail?.message || "An error occurred",
      detail?.video_id
    );
  }

  return response.json();
}

export function getExportUrl(
  videoId: string,
  format: string,
  languageCodes?: string[],
  mergeThreshold?: number
): string {
  const params = new URLSearchParams({
    video_id: videoId,
    format: format,
  });

  if (languageCodes?.length) {
    params.set("language_codes", languageCodes.join(","));
  }

  if (mergeThreshold !== undefined) {
    params.set("merge_threshold_seconds", mergeThreshold.toString());
  }

  return `${getApiUrl()}/transcript/export?${params.toString()}`;
}
