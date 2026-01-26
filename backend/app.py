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

@app.on_event("startup")
async def startup_event():
    global pipeline
    # Initialize singleton
    pipeline = AuditPipeline()

@app.post("/audit")
async def audit_text(request: AuditRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    if len(request.text) > 20000:
        raise HTTPException(status_code=400, detail="Text too long (max 20,000 characters).")
    
    try:
        if not pipeline:
            raise HTTPException(status_code=500, detail="Pipeline not initialized.")
            
        logger.info(f"Received audit request for text length: {len(request.text)}")
        result = pipeline.run(request.text)
        return result
    except Exception as e:
        logger.error(f"Audit Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
