"use client";

import { TranscriptResponse } from "@/lib/types";
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
  return (
    <div className="mt-6">
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
