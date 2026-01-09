"use client";

import { getExportUrl } from "@/lib/api";
import { ExportFormat } from "@/lib/types";

interface ExportButtonsProps {
  videoId: string;
  languageCodes?: string[];
  mergeThreshold?: number;
}

export default function ExportButtons({
  videoId,
  languageCodes,
  mergeThreshold,
}: ExportButtonsProps) {
  const handleExport = (format: ExportFormat) => {
    const url = getExportUrl(videoId, format, languageCodes, mergeThreshold);
    window.open(url, "_blank");
  };

  return (
    <div className="flex gap-2">
      <button
        onClick={() => handleExport("json")}
        className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
      >
        JSON
      </button>
      <button
        onClick={() => handleExport("txt")}
        className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
      >
        TXT
      </button>
      <button
        onClick={() => handleExport("srt")}
        className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
      >
        SRT
      </button>
    </div>
  );
}
