"""YouTube transcript extraction service layer."""

import re
import os
import logging
import concurrent.futures
from typing import Any

import yt_dlp
from cachetools import TTLCache
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours default
CACHE_MAX_SIZE = 100

transcript_cache: TTLCache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL)

# Video ID extraction patterns
YOUTUBE_PATTERNS = [
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})",
    r"^([a-zA-Z0-9_-]{11})$",  # Raw video ID
]


class TranscriptError(Exception):
    """Base exception for transcript errors."""
    def __init__(self, error_type: str, message: str, video_id: str | None = None):
        self.error_type = error_type
        self.message = message
        self.video_id = video_id
        super().__init__(message)


def extract_video_id(video_url_or_id: str) -> str:
    """Extract YouTube video ID from URL or raw ID."""
    video_url_or_id = video_url_or_id.strip()
    
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, video_url_or_id)
        if match:
            return match.group(1)
    
    raise TranscriptError(
        error_type="InvalidVideoId",
        message=f"Could not extract video ID from: {video_url_or_id[:50]}",
    )


def sanitize_video_id(video_id: str) -> str:
    """Validate and sanitize YouTube video ID."""
    # Remove any non-allowed characters
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", video_id)
    
    if len(sanitized) != 11:
        raise TranscriptError(
            error_type="InvalidVideoId",
            message=f"Invalid video ID format: {video_id[:20]}",
            video_id=video_id,
        )
    
    return sanitized


# Global API instance (thread-per-request is fine for our use case)
_api = YouTubeTranscriptApi()

# yt-dlp options for metadata extraction
_ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'extract_flat': False,
}


def fetch_video_metadata(video_id: str) -> dict[str, Any] | None:
    """Fetch video metadata from YouTube using yt-dlp."""
    try:
        with yt_dlp.YoutubeDL(_ydl_opts) as ydl:
            url = f"https://www.youtube.com/watch?v={video_id}"
            info = ydl.extract_info(url, download=False)
            
            # Format upload date from YYYYMMDD to YYYY-MM-DD
            upload_date = info.get('upload_date')
            if upload_date and len(upload_date) == 8:
                upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            
            return {
                'title': info.get('title', 'Unknown'),
                'channel': info.get('channel', info.get('uploader', 'Unknown')),
                'channel_url': info.get('channel_url', info.get('uploader_url', '')),
                'video_url': url,
                'upload_date': upload_date,
                'duration': info.get('duration'),
                'view_count': info.get('view_count'),
                'description': info.get('description'),
            }
    except Exception as e:
        logger.warning(f"Failed to fetch metadata for {video_id}: {e}")
        return None


def fetch_transcript(
    video_id: str,
    language_codes: list[str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Fetch transcript from YouTube with caching and timeout."""
    if language_codes is None:
        language_codes = ["en"]
    
    video_id = sanitize_video_id(video_id)
    cache_key = f"{video_id}:{','.join(language_codes)}"
    
    # Check cache first
    if cache_key in transcript_cache:
        return transcript_cache[cache_key]
    
    try:
        # Fetch with timeout using instance method
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                _api.fetch,
                video_id,
                languages=language_codes,
            )
            fetched = future.result(timeout=timeout)
        
        # Fetch metadata in parallel
        metadata = fetch_video_metadata(video_id)
        
        # The fetched result is a FetchedTranscript object with metadata
        result = {
            "video_id": video_id,
            "language_code": fetched.language_code,
            "is_generated": fetched.is_generated,
            "metadata": metadata,
            "segments": [
                {
                    "index": i,
                    "start": snippet.start,
                    "duration": snippet.duration,
                    "end": snippet.start + snippet.duration,
                    "text": snippet.text,
                }
                for i, snippet in enumerate(fetched.snippets)
            ],
        }
        
        # Cache the result
        transcript_cache[cache_key] = result
        return result
        
    except TranscriptsDisabled:
        raise TranscriptError(
            error_type="TranscriptsDisabled",
            message="Transcripts are disabled for this video",
            video_id=video_id,
        )
    except NoTranscriptFound:
        raise TranscriptError(
            error_type="NoTranscriptFound",
            message=f"No transcript available in languages: {language_codes}",
            video_id=video_id,
        )
    except VideoUnavailable:
        raise TranscriptError(
            error_type="VideoUnavailable",
            message="This video is unavailable or private",
            video_id=video_id,
        )
    except concurrent.futures.TimeoutError:
        raise TranscriptError(
            error_type="Timeout",
            message=f"Request timed out after {timeout} seconds",
            video_id=video_id,
        )
    except Exception as e:
        raise TranscriptError(
            error_type="UnexpectedError",
            message=str(e),
            video_id=video_id,
        )


def merge_segments(segments: list[dict], threshold: float) -> list[dict]:
    """Merge adjacent segments when gap is <= threshold."""
    if not segments or threshold <= 0:
        return segments
    
    merged = []
    current = None
    
    for seg in segments:
        if current is None:
            current = seg.copy()
        else:
            gap = seg["start"] - current["end"]
            if gap <= threshold:
                # Merge: extend duration and concatenate text
                current["end"] = seg["end"]
                current["duration"] = current["end"] - current["start"]
                current["text"] = current["text"] + " " + seg["text"]
            else:
                merged.append(current)
                current = seg.copy()
    
    if current is not None:
        merged.append(current)
    
    # Re-index
    for i, seg in enumerate(merged):
        seg["index"] = i
    
    return merged


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS,mmm for SRT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_txt(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for TXT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_export(segments: list[dict], format: str, video_id: str) -> tuple[str, str, str]:
    """Format segments for export. Returns (content, content_type, filename)."""
    if format == "json":
        import json
        content = json.dumps(segments, indent=2)
        return content, "application/json", f"{video_id}_transcript.json"
    
    elif format == "txt":
        lines = []
        for seg in segments:
            timestamp = format_timestamp_txt(seg["start"])
            lines.append(f"[{timestamp}] {seg['text']}")
        content = "\n".join(lines)
        return content, "text/plain", f"{video_id}_transcript.txt"
    
    elif format == "srt":
        lines = []
        for seg in segments:
            lines.append(str(seg["index"] + 1))
            start_ts = format_timestamp(seg["start"])
            end_ts = format_timestamp(seg["end"])
            lines.append(f"{start_ts} --> {end_ts}")
            lines.append(seg["text"])
            lines.append("")  # Blank line between entries
        content = "\n".join(lines)
        return content, "text/srt", f"{video_id}_transcript.srt"
    
    else:
        raise ValueError(f"Unsupported format: {format}")
