"use client";

import { Segment as SegmentType } from "@/lib/types";
import { formatTimestamp } from "@/lib/formatters";
import { useState } from "react";

interface SegmentProps {
  segment: SegmentType;
  videoId: string;
}

export default function Segment({ segment, videoId }: SegmentProps) {
  const [copied, setCopied] = useState(false);

  const handleTimestampClick = () => {
    const timestamp = formatTimestamp(segment.start);
    navigator.clipboard.writeText(timestamp);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const youtubeUrl = `https://youtube.com/watch?v=${videoId}&t=${Math.floor(
    segment.start
  )}`;

  return (
    <div className="flex gap-3 py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50">
      <div className="flex-shrink-0 w-24">
        <button
          onClick={handleTimestampClick}
          className="text-sm font-mono text-red-600 hover:text-red-800 hover:underline"
          title="Click to copy timestamp"
        >
          {copied ? "Copied!" : formatTimestamp(segment.start)}
        </button>
      </div>
      <div className="flex-1">
        <a
          href={youtubeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-800 hover:text-red-600"
        >
          {segment.text}
        </a>
      </div>
    </div>
  );
}
