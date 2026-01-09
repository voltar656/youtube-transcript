"use client";

import { useState } from "react";
import TranscriptForm from "@/components/TranscriptForm";
import TranscriptDisplay from "@/components/TranscriptDisplay";
import { fetchTranscript, ApiError } from "@/lib/api";
import { TranscriptResponse } from "@/lib/types";

export default function Home() {
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentSettings, setCurrentSettings] = useState<{
    languageCodes?: string[];
    mergeThreshold?: number;
  }>({});

  const handleSubmit = async (
    videoUrl: string,
    languageCodes: string[],
    mergeThreshold: number | undefined
  ) => {
    setIsLoading(true);
    setError(null);
    setTranscript(null);

    try {
      const result = await fetchTranscript({
        video_url: videoUrl,
        language_codes: languageCodes,
        merge_threshold_seconds: mergeThreshold,
      });
      setTranscript(result);
      setCurrentSettings({ languageCodes, mergeThreshold });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.error}: ${err.message}`);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen py-8">
      <div className="max-w-3xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            YouTube Transcript
          </h1>
          <p className="text-gray-600">
            Extract transcripts from any YouTube video
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <TranscriptForm onSubmit={handleSubmit} isLoading={isLoading} />

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {transcript && (
            <TranscriptDisplay
              transcript={transcript}
              languageCodes={currentSettings.languageCodes}
              mergeThreshold={currentSettings.mergeThreshold}
            />
          )}
        </div>

        <footer className="mt-8 text-center text-sm text-gray-500">
          <p>
            API docs available at{" "}
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-red-600 hover:underline"
            >
              /docs
            </a>
          </p>
        </footer>
      </div>
    </main>
  );
}
