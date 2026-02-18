import logging
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pipeline.run_full_audit import AuditPipeline
from core.audit_run_logger import AuditRunLogger, normalize_mode

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("epistemic_audit_engine")

app = FastAPI(title="Epistemic Audit Engine API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    text: str
    mode: Optional[str] = None

pipeline = None
PIPELINE_READY = False
START_TS = time.monotonic()
audit_logger = AuditRunLogger()


def _build_error_result(status_code: int, detail: str) -> dict:
    return {
        "status_code": status_code,
        "detail": detail,
    }


def _safe_log_audit_run(text: str, mode: str, result: dict, started_at: float, extra: Optional[dict] = None) -> None:
    metadata = {"request_wall_ms": int((time.perf_counter() - started_at) * 1000)}
    if extra:
        metadata.update(extra)
    audit_logger.log_run(
        input_text=text,
        mode=mode,
        result=result,
        extra_metadata=metadata,
    )

@app.on_event("startup")
async def startup_event():
    global pipeline, PIPELINE_READY
    # Initialize singleton
    pipeline = AuditPipeline()
    PIPELINE_READY = True
    configured_host = os.getenv("UVICORN_HOST") or os.getenv("HOST")
    configured_port = os.getenv("UVICORN_PORT") or os.getenv("PORT")

    if configured_host and configured_port:
        logger.info(
            "Backend ready pid=%s pipeline_ready=%s configured_host=%s configured_port=%s",
            os.getpid(),
            PIPELINE_READY,
            configured_host,
            configured_port,
        )
    elif configured_port:
        logger.info(
            "Backend ready pid=%s pipeline_ready=%s configured_port=%s",
            os.getpid(),
            PIPELINE_READY,
            configured_port,
        )
    elif configured_host:
        logger.info(
            "Backend ready pid=%s pipeline_ready=%s configured_host=%s",
            os.getpid(),
            PIPELINE_READY,
            configured_host,
        )
    else:
        logger.info(
            "Backend ready pid=%s pipeline_ready=%s",
            os.getpid(),
            PIPELINE_READY,
        )

@app.post("/audit")
async def audit_text(request: AuditRequest):
    request_started = time.perf_counter()
    mode = normalize_mode(request.mode)

    if not request.text.strip():
        detail = "Text cannot be empty."
        _safe_log_audit_run(
            text=request.text,
            mode=mode,
            result=_build_error_result(400, detail),
            started_at=request_started,
            extra={"error": "validation_error"},
        )
        raise HTTPException(status_code=400, detail=detail)

    if len(request.text) > 20000:
        detail = "Text too long (max 20,000 characters)."
        _safe_log_audit_run(
            text=request.text,
            mode=mode,
            result=_build_error_result(400, detail),
            started_at=request_started,
            extra={"error": "validation_error"},
        )
        raise HTTPException(status_code=400, detail=detail)

    try:
        if not PIPELINE_READY:
            detail = "Pipeline not ready."
            _safe_log_audit_run(
                text=request.text,
                mode=mode,
                result=_build_error_result(503, detail),
                started_at=request_started,
                extra={"error": "pipeline_not_ready"},
            )
            raise HTTPException(status_code=503, detail=detail)

        logger.info("Received audit request (len=%s, mode=%s)", len(request.text), mode)
        result = pipeline.run(request.text, mode=mode)
        _safe_log_audit_run(
            text=request.text,
            mode=mode,
            result=result,
            started_at=request_started,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        _safe_log_audit_run(
            text=request.text,
            mode=mode,
            result=_build_error_result(500, str(e)),
            started_at=request_started,
            extra={"error": "internal_error"},
        )
        logger.error(f"Audit Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    if not PIPELINE_READY:
        logger.warning("Health check requested before pipeline ready.")
    uptime_s = max(0.0, time.monotonic() - START_TS)
    return {
        "status": "ok",
        "pipeline_ready": PIPELINE_READY,
        "pid": os.getpid(),
        "uptime_s": round(uptime_s, 3),
    }
