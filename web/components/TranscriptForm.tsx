"use client";

import { useState } from "react";

interface TranscriptFormProps {
  onSubmit: (
    videoUrl: string,
    languageCodes: string[],
    mergeThreshold: number | undefined
  ) => void;
  isLoading: boolean;
}

export default function TranscriptForm({
  onSubmit,
  isLoading,
}: TranscriptFormProps) {
  const [videoUrl, setVideoUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [mergeThreshold, setMergeThreshold] = useState<string>("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoUrl.trim()) return;

    const threshold = mergeThreshold ? parseFloat(mergeThreshold) : undefined;
    onSubmit(videoUrl.trim(), [language], threshold);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label
          htmlFor="videoUrl"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          YouTube URL or Video ID
        </label>
        <input
          type="text"
          id="videoUrl"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.currentTarget.value)}
          placeholder="https://youtube.com/watch?v=... or video ID"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
          disabled={isLoading}
        />
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label
            htmlFor="language"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            disabled={isLoading}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="pt">Portuguese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
        </div>

        <div className="flex-1">
          <label
            htmlFor="mergeThreshold"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Merge Threshold (seconds)
          </label>
          <input
            type="number"
            id="mergeThreshold"
            value={mergeThreshold}
            onChange={(e) => setMergeThreshold(e.target.value)}
            placeholder="e.g., 1.5"
            min="0"
            max="60"
            step="0.5"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading || !videoUrl.trim()}
        className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Fetching...
          </span>
        ) : (
          "Get Transcript"
        )}
      </button>
    </form>
  );
}
