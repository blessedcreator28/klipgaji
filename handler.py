import runpod
import os
import uuid
import subprocess
import whisper
import boto3
import torch
from supabase import create_client

# Log start
print("🔥 HANDLER STARTING", flush=True)

s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

print("🔥 LOADING MODEL...", flush=True)
model = whisper.load_model('small', download_root='/app/models')
print("✅ MODEL LOADED", flush=True)

def handler(job):
    print("🔥 JOB STARTED", flush=True)
    try:
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        filename = video_url.split('/')[-1]
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        # Download
        print(f"📥 DOWNLOAD START: {filename}", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        print("✅ DOWNLOAD FINISHED", flush=True)
        
        # Konversi Audio
        print("🎧 FFMPEG STARTING...", flush=True)
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        print("✅ FFMPEG FINISHED", flush=True)
        
        # BERSIHKAN MEMORI
        torch.cuda.empty_cache()
        
        # Transcribe
        print("🤖 AI TRANSCRIBE STARTING...", flush=True)
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        print("✅ TRANSCRIBE FINISHED", flush=True)
        
        return {"status": "success", "message": "Done"}
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})