import os
import uuid
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
app = FastAPI()

# Config
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Config RunPod
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID")
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class VideoRequest(BaseModel):
    user_id: str = "string"
    youtube_url: str

@app.post("/api/v1/generate")
async def generate_clips(request: VideoRequest):
    job_id = str(uuid.uuid4())
    
    # 1. Insert ke Supabase
    supabase.table("jobs").insert({
        "id": job_id,
        "input_url": request.youtube_url,
        "status": "pending"
    }).execute()
    
    # 2. Trigger RunPod API
    runpod_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    payload = {
        "input": {
            "job_id": job_id,
            "s3_key": request.youtube_url
        }
    }
    
    try:
        response = requests.post(runpod_url, json=payload, headers=headers)
        # Print diagnostik agar kita tahu ada masalah apa
        print(f"[API] RunPod Response Code: {response.status_code}")
        print(f"[API] RunPod Response Body: {response.text}")
        
        return {"status": "Queued", "job_id": job_id, "runpod_status": response.status_code}
    except Exception as e:
        print(f"Error triggering RunPod: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)