"use client";

import { TranscriptResponse, VideoMetadata } from "@/lib/types";
import { formatDuration } from "@/lib/formatters";
import Segment from "./Segment";
import ExportButtons from "./ExportButtons";

interface TranscriptDisplayProps {
  transcript: TranscriptResponse;
  languageCodes?: string[];
  mergeThreshold?: number;
}

export default function TranscriptDisplay({
  transcript,
  languageCodes,
  mergeThreshold,
}: TranscriptDisplayProps) {
  const meta = transcript.metadata;

  return (
    <div className="mt-6">
      {/* Video Metadata */}
      {meta && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            <a
              href={meta.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-red-600"
            >
              {meta.title}
            </a>
          </h2>
          <div className="text-sm text-gray-600 space-y-1">
            <p>
              <span className="font-medium">Channel:</span>{" "}
              <a
                href={meta.channel_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-red-600 hover:underline"
              >
                {meta.channel}
              </a>
            </p>
            <p>
              {meta.upload_date && (
                <span>
                  <span className="font-medium">Published:</span> {meta.upload_date}
                </span>
              )}
              {meta.duration && (
                <span className="ml-4">
                  <span className="font-medium">Duration:</span> {formatDuration(meta.duration)}
                </span>
              )}
              {meta.view_count && (
                <span className="ml-4">
                  <span className="font-medium">Views:</span> {meta.view_count.toLocaleString()}
                </span>
              )}
            </p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Transcript
          </h2>
          <p className="text-sm text-gray-500">
            {transcript.segments.length} segments •{" "}
            {transcript.language_code.toUpperCase()} •{" "}
            {transcript.is_generated ? "Auto-generated" : "Manual"}
          </p>
        </div>
        <ExportButtons
          videoId={transcript.video_id}
          languageCodes={languageCodes}
          mergeThreshold={mergeThreshold}
        />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="max-h-[500px] overflow-y-auto p-4">
          {transcript.segments.map((segment) => (
            <Segment
              key={segment.index}
              segment={segment}
              videoId={transcript.video_id}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
