import runpod
import os
import uuid
import subprocess
import whisper
import boto3
import torch
import sys
from supabase import create_client

# Force log agar tidak tersumbat/buffer
sys.stdout.reconfigure(line_buffering=True)
print("--- [DEBUG] LOGGER INITIALIZED ---", flush=True)

# Cek env
required_envs = ['R2_ENDPOINT', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'R2_BUCKET']
for env in required_envs:
    if env not in os.environ:
        print(f"--- [ERROR] MISSING ENV: {env} ---", flush=True)
        raise Exception(f"Missing env: {env}")

# Init R2
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

print("--- [DEBUG] LOADING MODEL... ---", flush=True)
model = whisper.load_model('small', download_root='/app/models')
print("--- [DEBUG] MODEL LOADED SUCCESSFULLY ---", flush=True)

def handler(job):
    print(f"--- [DEBUG] JOB RECEIVED: {job.get('id')} ---", flush=True)
    try:
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        filename = video_url.split('/')[-1]
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        # Download & Verifikasi
        print(f"--- [DEBUG] STARTING DOWNLOAD: {filename} ---", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            print(f"--- [DEBUG] DOWNLOAD COMPLETE. File Size: {file_size} bytes ---", flush=True)
        else:
            raise Exception("File download failed, file not found on disk")
        
        # FFmpeg dengan logging
        print("--- [DEBUG] STARTING FFMPEG ---", flush=True)
        # Menambah -v error agar tidak spam, tapi tetap muncul kalau gagal
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("--- [DEBUG] FFMPEG FINISHED ---", flush=True)
        
        torch.cuda.empty_cache()
        
        print("--- [DEBUG] STARTING TRANSCRIBE ---", flush=True)
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        print(f"--- [DEBUG] TRANSCRIBE FINISHED. Result keys: {result.keys()} ---", flush=True)
        
        return {"status": "success", "message": "Done"}
        
    except subprocess.CalledProcessError as e:
        print(f"--- [ERROR] FFMPEG CRASHED: {e.stderr} ---", flush=True)
        return {"status": "error", "message": str(e.stderr)}
    except Exception as e:
        print(f"--- [ERROR] CRITICAL: {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})