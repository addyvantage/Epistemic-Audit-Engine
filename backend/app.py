import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
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

pipeline = None
PIPELINE_READY = False

@app.on_event("startup")
async def startup_event():
    global pipeline, PIPELINE_READY
    # Initialize singleton
    pipeline = AuditPipeline()
    PIPELINE_READY = True

@app.post("/audit")
async def audit_text(request: AuditRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    if len(request.text) > 20000:
        raise HTTPException(status_code=400, detail="Text too long (max 20,000 characters).")
    
    try:
        if not PIPELINE_READY:
            raise HTTPException(status_code=503, detail="Pipeline not ready.")
            
        logger.info(f"Received audit request for text length: {len(request.text)}")
        result = pipeline.run(request.text)
        return result
    except Exception as e:
        logger.error(f"Audit Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    if not PIPELINE_READY:
        raise HTTPException(status_code=503, detail="Pipeline loading")
    return {"status": "ready"}
