cat <<EOF > handler.py
import runpod
import os
import boto3
import sys
import subprocess

# Konfigurasi log
sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

def handler(job):
    print(f"--- [HANDLER] JOB RECEIVED: {job.get('id')} ---", flush=True)
    
    try:
        # Inisialisasi S3
        s3 = boto3.client('s3',
            endpoint_url=os.environ['R2_ENDPOINT'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name='auto'
        )
        
        job_input = job.get('input', {})
        video_url = job_input.get('video_url', '')
        filename = video_url.split('/')[-1]
        video_path = f"/tmp/{filename}"
        audio_path = f"/tmp/{filename.replace('.mp4', '.wav')}"
        
        # 1. DOWNLOAD
        print(f"--- [DOWNLOAD] START: {filename} ---", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        print(f"--- [DOWNLOAD] SUCCESS ---", flush=True)
        
        # 2. FFMPEG (Extract Audio)
        print("--- [FFMPEG] START EXTRACT AUDIO ---", flush=True)
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ], check=True)
        print(f"--- [FFMPEG] SUCCESS: Audio created at {audio_path} ---", flush=True)
        
        return {"status": "success", "message": "Download & FFmpeg successful"}
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR] {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
EOF