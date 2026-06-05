import runpod
import os
import uuid
import subprocess
import whisper
import boto3
import torch
import sys
from supabase import create_client

sys.stdout.reconfigure(line_buffering=True)

s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

print("--- [DEBUG] LOADING MODEL... ---", flush=True)
model = whisper.load_model('small', download_root='/app/models')
print("--- [DEBUG] MODEL LOADED ---", flush=True)

def handler(job):
    print("--- [DEBUG] JOB START ---", flush=True)
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
        # Hapus capture_output biar log langsung ke dashboard
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        print("--- [DEBUG] FFMPEG SUCCESS ---", flush=True)
        
        print("--- [DEBUG] TRANSCRIBE START ---", flush=True)
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        print("--- [DEBUG] TRANSCRIBE SUCCESS ---", flush=True)
        
        # ... (Logika clipping & upload tetap di bawah sini) ...
        
        return {"status": "success", "message": "Done"}
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR] {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})