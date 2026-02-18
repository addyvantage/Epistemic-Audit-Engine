import logging
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pipeline.run_full_audit import AuditPipeline

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
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    if len(request.text) > 20000:
        raise HTTPException(status_code=400, detail="Text too long (max 20,000 characters).")
    
    try:
        if not PIPELINE_READY:
            raise HTTPException(status_code=503, detail="Pipeline not ready.")
            
        mode = (request.mode or "research").strip().lower() or "research"
        logger.info("Received audit request (len=%s, mode=%s)", len(request.text), mode)
        result = pipeline.run(request.text, mode=mode)
        return result
    except Exception as e:
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
