"""FastAPI application for YouTube transcript extraction."""

import os
import logging
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import (
    TranscriptRequest,
    TranscriptResponse,
    Segment,
    ErrorResponse,
    HealthResponse,
)
from app.service import (
    extract_video_id,
    fetch_transcript,
    merge_segments,
    format_export,
    TranscriptError,
)

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Request ID context
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

# Rate limiting
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "30")
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="YouTube Transcript API",
    description="Extract transcripts from YouTube videos",
    version="0.1.0",
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with request ID."""
    request_id = str(uuid.uuid4())[:8]
    request_id_ctx.set(request_id)
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(f"[{request_id}] Response: {response.status_code}")
    
    return response


def map_error_to_status(error_type: str) -> int:
    """Map error types to HTTP status codes."""
    mapping = {
        "InvalidVideoId": 400,
        "TranscriptsDisabled": 403,
        "NoTranscriptFound": 404,
        "VideoUnavailable": 404,
        "Timeout": 504,
        "UnexpectedError": 500,
    }
    return mapping.get(error_type, 500)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post(
    "/transcript",
    response_model=TranscriptResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def get_transcript(request: Request, body: TranscriptRequest):
    """Fetch transcript for a YouTube video."""
    try:
        # Extract video ID
        video_input = body.video_url or body.video_id
        video_id = extract_video_id(video_input)
        
        logger.info(f"[{request_id_ctx.get()}] Fetching transcript for {video_id}")
        
        # Fetch transcript
        result = fetch_transcript(
            video_id=video_id,
            language_codes=body.language_codes,
        )
        
        segments = result["segments"]
        
        # Merge if requested
        if body.merge_threshold_seconds:
            segments = merge_segments(segments, body.merge_threshold_seconds)
        
        logger.info(
            f"[{request_id_ctx.get()}] Fetched {len(segments)} segments for {video_id}"
        )
        
        return TranscriptResponse(
            video_id=result["video_id"],
            language_code=result["language_code"],
            is_generated=result["is_generated"],
            segments=[Segment(**seg) for seg in segments],
        )
        
    except TranscriptError as e:
        logger.warning(f"[{request_id_ctx.get()}] {e.error_type}: {e.message}")
        raise HTTPException(
            status_code=map_error_to_status(e.error_type),
            detail=ErrorResponse(
                error=e.error_type,
                message=e.message,
                video_id=e.video_id,
            ).model_dump(),
        )
    except Exception as e:
        logger.exception(f"[{request_id_ctx.get()}] Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="UnexpectedError",
                message="An unexpected error occurred",
            ).model_dump(),
        )


@app.get("/transcript/export")
@limiter.limit(f"{RATE_LIMIT}/minute")
async def export_transcript(
    request: Request,
    video_id: str = Query(..., description="YouTube video ID"),
    format: str = Query("json", pattern="^(json|txt|srt)$", description="Export format"),
    language_codes: str = Query("en", description="Comma-separated language codes"),
    merge_threshold_seconds: float | None = Query(None, description="Merge threshold"),
):
    """Export transcript in various formats."""
    try:
        langs = [l.strip() for l in language_codes.split(",") if l.strip()]
        
        logger.info(f"[{request_id_ctx.get()}] Exporting {format} for {video_id}")
        
        # Fetch transcript
        result = fetch_transcript(
            video_id=video_id,
            language_codes=langs,
        )
        
        segments = result["segments"]
        
        # Merge if requested
        if merge_threshold_seconds:
            segments = merge_segments(segments, merge_threshold_seconds)
        
        # Format export
        content, content_type, filename = format_export(segments, format, video_id)
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
        
    except TranscriptError as e:
        logger.warning(f"[{request_id_ctx.get()}] {e.error_type}: {e.message}")
        raise HTTPException(
            status_code=map_error_to_status(e.error_type),
            detail=ErrorResponse(
                error=e.error_type,
                message=e.message,
                video_id=e.video_id,
            ).model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
