import runpod
import os
import uuid
import subprocess
import whisper
import boto3
import torch
import sys
from supabase import create_client

# Force unbuffered logging
sys.stdout.reconfigure(line_buffering=True)
print("--- [SYSTEM] STARTING WORKER (GPU MODE) ---", flush=True)

# Inisialisasi
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

# PAKSA PAKAI GPU
print("--- [DEBUG] LOADING MODEL TO GPU... ---", flush=True)
model = whisper.load_model('small', device='cuda', download_root='/app/models')
print("--- [DEBUG] MODEL LOADED ON GPU SUCCESSFULLY ---", flush=True)

def handler(job):
    print(f"--- [JOB] {job.get('id')} RECEIVED ---", flush=True)
    try:
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        filename = video_url.split('/')[-1]
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        print(f"--- [DEBUG] DOWNLOAD: {filename} ---", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        print("--- [DEBUG] FFMPEG START ---", flush=True)
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        print("--- [DEBUG] FFMPEG SUCCESS ---", flush=True)
        
        # TRANSKRIPSI PAKSA GPU & FP16 FALSE (Biar nggak rewel)
        print("--- [DEBUG] TRANSCRIBE START (GPU) ---", flush=True)
        result = model.transcribe(audio_path, language="id", word_timestamps=True, fp16=False)
        print("--- [DEBUG] TRANSCRIBE SUCCESS ---", flush=True)
        
        return {"status": "success", "message": "Done"}
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR] {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})