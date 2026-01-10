export interface Segment {
  index: number;
  start: number;
  duration: number;
  end: number;
  text: string;
}

export interface VideoMetadata {
  title: string;
  channel: string;
  channel_url: string;
  video_url: string;
  upload_date?: string;
  duration?: number;
  view_count?: number;
  description?: string;
}

export interface TranscriptResponse {
  video_id: string;
  language_code: string;
  is_generated: boolean;
  metadata?: VideoMetadata;
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
