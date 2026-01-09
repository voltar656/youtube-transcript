"""Tests for service layer functions."""

import pytest
from app.service import (
    extract_video_id,
    sanitize_video_id,
    merge_segments,
    format_export,
    format_timestamp,
    format_timestamp_txt,
    TranscriptError,
)


class TestExtractVideoId:
    """Tests for extract_video_id function."""

    def test_full_youtube_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_youtube_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_raw_video_id(self):
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        with pytest.raises(TranscriptError) as exc:
            extract_video_id("not-a-valid-url")
        assert exc.value.error_type == "InvalidVideoId"

    def test_whitespace_handling(self):
        assert extract_video_id("  dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"


class TestSanitizeVideoId:
    """Tests for sanitize_video_id function."""

    def test_valid_id(self):
        assert sanitize_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_id_with_dash(self):
        assert sanitize_video_id("abc-def_123") == "abc-def_123"

    def test_invalid_length(self):
        with pytest.raises(TranscriptError) as exc:
            sanitize_video_id("short")
        assert exc.value.error_type == "InvalidVideoId"

    def test_strips_invalid_chars(self):
        with pytest.raises(TranscriptError):
            sanitize_video_id("abc!def@ghi")  # After stripping, too short


class TestMergeSegments:
    """Tests for merge_segments function."""

    def test_no_merge_needed(self):
        segments = [
            {"index": 0, "start": 0.0, "end": 2.0, "duration": 2.0, "text": "Hello"},
            {"index": 1, "start": 5.0, "end": 7.0, "duration": 2.0, "text": "World"},
        ]
        result = merge_segments(segments, threshold=1.0)
        assert len(result) == 2

    def test_merge_adjacent(self):
        segments = [
            {"index": 0, "start": 0.0, "end": 2.0, "duration": 2.0, "text": "Hello"},
            {"index": 1, "start": 2.5, "end": 4.5, "duration": 2.0, "text": "World"},
        ]
        result = merge_segments(segments, threshold=1.0)
        assert len(result) == 1
        assert result[0]["text"] == "Hello World"
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 4.5

    def test_empty_segments(self):
        assert merge_segments([], threshold=1.0) == []

    def test_zero_threshold(self):
        segments = [
            {"index": 0, "start": 0.0, "end": 2.0, "duration": 2.0, "text": "Hello"},
        ]
        result = merge_segments(segments, threshold=0)
        assert len(result) == 1

    def test_reindex_after_merge(self):
        segments = [
            {"index": 0, "start": 0.0, "end": 1.0, "duration": 1.0, "text": "A"},
            {"index": 1, "start": 1.2, "end": 2.0, "duration": 0.8, "text": "B"},
            {"index": 2, "start": 5.0, "end": 6.0, "duration": 1.0, "text": "C"},
        ]
        result = merge_segments(segments, threshold=0.5)
        assert result[0]["index"] == 0
        assert result[1]["index"] == 1


class TestFormatTimestamp:
    """Tests for timestamp formatting."""

    def test_format_timestamp_srt(self):
        assert format_timestamp(0) == "00:00:00,000"
        assert format_timestamp(61.5) == "00:01:01,500"
        assert format_timestamp(3661.123) == "01:01:01,123"

    def test_format_timestamp_txt(self):
        assert format_timestamp_txt(0) == "00:00:00.000"
        assert format_timestamp_txt(61.5) == "00:01:01.500"


class TestFormatExport:
    """Tests for format_export function."""

    @pytest.fixture
    def sample_segments(self):
        return [
            {"index": 0, "start": 0.0, "end": 2.0, "duration": 2.0, "text": "Hello"},
            {"index": 1, "start": 2.5, "end": 4.5, "duration": 2.0, "text": "World"},
        ]

    def test_json_format(self, sample_segments):
        content, content_type, filename = format_export(
            sample_segments, "json", "test123"
        )
        assert content_type == "application/json"
        assert filename == "test123_transcript.json"
        assert "Hello" in content

    def test_txt_format(self, sample_segments):
        content, content_type, filename = format_export(
            sample_segments, "txt", "test123"
        )
        assert content_type == "text/plain"
        assert filename == "test123_transcript.txt"
        assert "[00:00:00.000] Hello" in content

    def test_srt_format(self, sample_segments):
        content, content_type, filename = format_export(
            sample_segments, "srt", "test123"
        )
        assert content_type == "text/srt"
        assert filename == "test123_transcript.srt"
        assert "00:00:00,000 --> 00:00:02,000" in content

    def test_invalid_format(self, sample_segments):
        with pytest.raises(ValueError):
            format_export(sample_segments, "invalid", "test123")
