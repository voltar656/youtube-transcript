export interface Segment {
  index: number;
  start: number;
  duration: number;
  end: number;
  text: string;
}

export interface TranscriptResponse {
  video_id: string;
  language_code: string;
  is_generated: boolean;
  segments: Segment[];
}

export interface TranscriptRequest {
  video_url?: string;
  video_id?: string;
  language_codes?: string[];
  merge_threshold_seconds?: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  video_id?: string;
}

export type ExportFormat = "json" | "txt" | "srt";
