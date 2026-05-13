from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from worker import process_video_task
import uuid

app = FastAPI()

# FIX CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sesuaikan dengan skema JSON di dashboard lo (ada user_id)
class VideoRequest(BaseModel):
    user_id: str = "string"
    youtube_url: str

@app.get("/")
async def read_root():
    return {"status": "Clipper Engine Online"}

# PINTU UTAMA: Sesuaikan dengan Dashboard lo
@app.post("/api/v1/generate")
async def generate_clips(request: VideoRequest):
    job_id = str(uuid.uuid4())
    print(f"[API] Sync Success! User: {request.user_id} | Job: {job_id}")
    
    # Kirim ke Celery Worker
    process_video_task.delay(job_id, request.youtube_url)
    
    return {
        "status": "Queued", 
        "job_id": job_id,
        "message": "Generating viral clips..."
    }

# Backup pintu lama biar nggak bingung
@app.post("/process")
async def process_legacy(request: VideoRequest):
    return await generate_clips(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)