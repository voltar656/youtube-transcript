# TASKS.md

Tracks implementation tasks for the YouTube Transcript project.

## MVP (Script)

Goal: a pipe-friendly CLI that prints transcript *text only* to stdout.

- [x] Create `transcript.py` with args:
  - Positional: `url_or_id`
  - `--lang en` (repeatable; default `en`)
  - `--merge-threshold-seconds FLOAT` (optional; merge adjacent segments)
  - `--format {text,jsonl}` (default `text`)
- [x] `text` format prints a single plain-text transcript (no timestamps).
- [x] `jsonl` format prints one segment per line with `start`, `duration`, `text`.
- [x] Exit codes + messages:
  - 2: invalid URL/ID
  - 3: transcripts disabled/private
  - 4: no transcript found
  - 5: unexpected error
- [x] Usage examples:
  - `python3 transcript.py "https://youtu.be/VIDEO_ID"`
  - `python3 transcript.py VIDEO_ID --lang en --lang es`
  - `python3 transcript.py VIDEO_ID --format jsonl | jq -r .text | sed ...`
  - `python3 transcript.py VIDEO_ID | pbcopy`

## Backend Core Setup

- [x] Initialize project with `uv` targeting Python 3.11+.
- [x] Add dependencies: `fastapi[standard]`, `uvicorn[standard]`, `youtube-transcript-api`
- [x] Add new dependencies: `cachetools`, `slowapi`, `python-multipart`
- [x] Implement directory layout: `app/main.py`, `app/models.py`, `app/service.py`

## Backend Service Layer

- [x] Implement `extract_video_id()` robustly (full URL, short URL, embed URL, raw ID)
- [x] Implement `fetch_transcript(video_id, language_codes)` with 30s timeout
- [x] Add in-memory caching with TTL (100 items, 24h)
- [x] Implement optional `merge_segments(segments, threshold)`
- [x] Implement `format_export(segments, format, video_id)` for JSON, TXT, SRT
- [x] Add `sanitize_video_id()` validation (alphanumeric, dash, underscore only)
- [x] Map `youtube-transcript-api` errors → stable HTTP status codes (403, 404, 500)

## Backend API Layer

- [x] Define Pydantic models: `TranscriptRequest`, `TranscriptResponse`, `Segment`, `ErrorResponse`
- [x] Add input validation with `field_validator` (length check, mutual exclusivity of url/id)
- [x] Implement `/health` endpoint
- [x] Implement `POST /transcript` with stable schema
- [x] Implement `GET /transcript/export` (query params: `video_id`, `format`)
- [x] Add CORS middleware with `ALLOWED_ORIGINS`
- [x] Add GZip compression middleware (minimum_size=1000)
- [x] Add rate limiting with `slowapi` (30 req/min default)
- [x] Add structured JSON logging with request IDs (simple implementation)

## Backend Tests

- [x] Unit tests for `extract_video_id`
- [x] Unit tests for `merge_segments`
- [x] Unit tests for `format_export` (JSON, TXT, SRT formats)
- [x] Unit tests for `sanitize_video_id`
- [ ] Integration test for `fetch_transcript` using known public video ID

## Backend Deployment

- [x] Add `Dockerfile` (python:3.12-slim, non-root user, uvicorn entrypoint)
- [x] Add backend service to `docker-compose.yml`
- [x] Configure environment variables in `docker-compose.yml`
- [x] Add healthcheck to backend service
- [x] Document build and run commands

## Frontend Core Setup

- [x] Initialize Next.js project with TypeScript and App Router
- [x] Add Tailwind CSS configuration
- [x] Create directory structure: `app/`, `components/`, `lib/`
- [x] Configure `NEXT_PUBLIC_API_URL` environment variable
- [ ] Add Vitest for testing

## Frontend Components

- [ ] Create `ErrorBoundary` component for error handling
- [x] Create `TranscriptForm` component (URL/ID input, language selector, merge threshold)
- [x] Create `TranscriptDisplay` component (segments list)
- [x] Create `Segment` component (individual segment with timestamp)
- [x] Create `ExportButtons` component (JSON, TXT, SRT buttons)

## Frontend Integration

- [x] Implement API client functions in `lib/api.ts`
- [x] Implement format formatters in `lib/formatters.ts`
- [x] Integrate components in `page.tsx`
- [ ] Wrap main page with `ErrorBoundary` in `layout.tsx`
- [x] Add loading states and error handling
- [x] Add copy-to-clipboard functionality for timestamps

## Frontend Tests

- [ ] Add unit tests for API client functions
- [ ] Add unit tests for format formatters
- [ ] Add unit tests for utility functions
- [ ] Configure Vitest with TypeScript support

## Documentation

- [x] Update README with quick start guide
- [x] Document environment variables (backend and frontend)
- [x] Document API endpoints (available at `/docs`)
- [x] Document Docker Compose usage
- [ ] Document monitoring and maintenance procedures
- [ ] Document export formats and use cases
