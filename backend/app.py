from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline.run_full_audit import AuditPipeline

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
    
    try:
        if not pipeline:
            raise HTTPException(status_code=500, detail="Pipeline not initialized.")
            
        result = pipeline.run(request.text)
        return result
    except Exception as e:
        print(f"Audit Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
