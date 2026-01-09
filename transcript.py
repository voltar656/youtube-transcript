#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Pipe-friendly YouTube transcript downloader.

Prints transcript content to stdout so it can be piped elsewhere.

Examples:
  python3 transcript.py "https://youtu.be/dQw4w9WgXcQ"
  python3 transcript.py dQw4w9WgXcQ --lang en --lang es
  python3 transcript.py dQw4w9WgXcQ --format jsonl | jq -r .text

Exit codes:
  2: invalid URL/ID
  3: transcripts disabled/private
  4: no transcript found
  5: unexpected error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (  # type: ignore
        AgeRestricted,
        InvalidVideoId,
        IpBlocked,
        NoTranscriptFound,
        RequestBlocked,
        TranscriptsDisabled,
        VideoUnavailable,
    )
except ModuleNotFoundError:  # pragma: no cover
    YouTubeTranscriptApi = None  # type: ignore[assignment]
    AgeRestricted = Exception  # type: ignore[misc,assignment]
    InvalidVideoId = Exception  # type: ignore[misc,assignment]
    IpBlocked = Exception  # type: ignore[misc,assignment]
    NoTranscriptFound = Exception  # type: ignore[misc,assignment]
    RequestBlocked = Exception  # type: ignore[misc,assignment]
    TranscriptsDisabled = Exception  # type: ignore[misc,assignment]
    VideoUnavailable = Exception  # type: ignore[misc,assignment]


_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


@dataclass(frozen=True)
class Segment:
    start: float
    duration: float
    text: str


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcript.py",
        description="Fetch a YouTube transcript and print to stdout.",
    )

    parser.add_argument(
        "url_or_id",
        help="YouTube video URL (watch, youtu.be, embed) or raw video id.",
    )

    parser.add_argument(
        "--lang",
        action="append",
        dest="language_codes",
        default=None,
        help="Language code to prefer (repeatable). Default: en.",
    )

    parser.add_argument(
        "--merge-threshold-seconds",
        type=float,
        default=None,
        help="If set, merge adjacent segments when the gap between them is <= threshold.",
    )

    parser.add_argument(
        "--format",
        choices=("text", "jsonl"),
        default="text",
        help="Output format. text=plain transcript; jsonl=one segment per line.",
    )

    return parser


def extract_video_id(url_or_id: str) -> str:
    """Extract the YouTube video id from a URL, or return the raw ID.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - raw VIDEO_ID
    """

    candidate = url_or_id.strip()

    if _VIDEO_ID_RE.fullmatch(candidate):
        return candidate

    watch = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", candidate)
    if watch:
        return watch.group(1)

    short = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", candidate)
    if short:
        return short.group(1)

    embed = re.search(r"/embed/([a-zA-Z0-9_-]{11})", candidate)
    if embed:
        return embed.group(1)

    # Fallback: last path segment if it looks plausible
    path_id = re.search(r"/([a-zA-Z0-9_-]{11})(?:\?|$)", candidate)
    if path_id:
        return path_id.group(1)

    raise ValueError(f"Could not extract video id from input: {url_or_id!r}")


def fetch_segments(video_id: str, language_codes: list[str] | None) -> list[Segment]:
    if YouTubeTranscriptApi is None:  # pragma: no cover
        raise RuntimeError(
            "youtube-transcript-api is not installed. Install with: uv add youtube-transcript-api"
        )

    languages = language_codes or ["en"]

    transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    raw = transcript.to_raw_data()

    segments: list[Segment] = []
    for item in raw:
        segments.append(
            Segment(
                start=float(item["start"]),
                duration=float(item["duration"]),
                text=str(item["text"]).strip(),
            )
        )

    return segments


def merge_segments(segments: list[Segment], threshold_seconds: float) -> list[Segment]:
    if not segments:
        return []

    merged: list[Segment] = []
    current = segments[0]

    for nxt in segments[1:]:
        current_end = current.start + current.duration
        gap = nxt.start - current_end

        if gap <= threshold_seconds:
            new_text = (current.text + " " + nxt.text).strip()
            new_start = current.start
            new_end = max(current_end, nxt.start + nxt.duration)
            current = Segment(
                start=new_start, duration=new_end - new_start, text=new_text
            )
        else:
            merged.append(current)
            current = nxt

    merged.append(current)
    return merged


def _print_text(segments: list[Segment]) -> None:
    # Avoid blank lines; print a single transcript.
    transcript_text = "\n".join(s.text for s in segments if s.text)
    sys.stdout.write(transcript_text)
    if transcript_text and not transcript_text.endswith("\n"):
        sys.stdout.write("\n")


def _print_jsonl(segments: list[Segment]) -> None:
    for seg in segments:
        sys.stdout.write(
            json.dumps(
                {
                    "start": seg.start,
                    "duration": seg.duration,
                    "text": seg.text,
                },
                ensure_ascii=False,
            )
        )
        sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        video_id = extract_video_id(args.url_or_id)
    except ValueError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 2

    try:
        segments = fetch_segments(video_id, args.language_codes)
        if args.merge_threshold_seconds is not None:
            segments = merge_segments(segments, args.merge_threshold_seconds)

        if args.format == "jsonl":
            _print_jsonl(segments)
        else:
            _print_text(segments)

        return 0

    except InvalidVideoId:
        sys.stderr.write("ERROR: invalid video id (pass the 11-char ID, not a URL)\n")
        return 2
    except VideoUnavailable:
        sys.stderr.write("ERROR: video unavailable\n")
        return 2
    except (TranscriptsDisabled, AgeRestricted):
        sys.stderr.write("ERROR: transcripts are disabled/restricted for this video\n")
        return 3
    except NoTranscriptFound:
        sys.stderr.write("ERROR: no transcript found (try different --lang)\n")
        return 4
    except (RequestBlocked, IpBlocked):
        sys.stderr.write(
            "ERROR: request blocked / IP blocked by YouTube (try again later or use proxies)\n"
        )
        return 5
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"ERROR: unexpected failure: {e}\n")
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
