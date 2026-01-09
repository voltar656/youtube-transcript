"""Pydantic models for request/response validation."""

from pydantic import BaseModel, field_validator, model_validator


class Segment(BaseModel):
    """A single transcript segment."""
    index: int
    start: float
    duration: float
    end: float
    text: str


class TranscriptRequest(BaseModel):
    """Request model for transcript fetching."""
    video_url: str | None = None
    video_id: str | None = None
    language_codes: list[str] | None = None
    merge_threshold_seconds: float | None = None

    @model_validator(mode="after")
    def validate_video_identifier(self):
        if not self.video_url and not self.video_id:
            raise ValueError("Either video_url or video_id must be provided")
        return self

    @field_validator("video_url", "video_id", mode="before")
    @classmethod
    def validate_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("Video identifier too long")
        return v

    @field_validator("merge_threshold_seconds", mode="before")
    @classmethod
    def validate_threshold(cls, v):
        if v is not None and (v < 0 or v > 60):
            raise ValueError("Merge threshold must be between 0 and 60 seconds")
        return v


class TranscriptResponse(BaseModel):
    """Response model for transcript data."""
    video_id: str
    language_code: str
    is_generated: bool
    segments: list[Segment]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    video_id: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
