import runpod
import os
import boto3
import sys
import subprocess
import traceback  # Biar kita tahu persis di mana error-nya

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
        
        print(f"--- [DOWNLOAD] START: {filename} ---", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        print(f"--- [DOWNLOAD] SUCCESS ---", flush=True)
        
        # Cek apakah file ada
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} tidak ditemukan setelah download!")

        # 2. FFMPEG (Extract Audio)
        print("--- [FFMPEG] START EXTRACT AUDIO ---", flush=True)
        # Kita pakai capture_output=True biar error FFmpeg nggak bikin crash worker
        result = subprocess.run([
            "ffmpeg", "-y", "-i", video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"--- [FFMPEG ERROR] {result.stderr} ---", flush=True)
            return {"status": "error", "message": result.stderr}
            
        print(f"--- [FFMPEG] SUCCESS: Audio created ---", flush=True)
        return {"status": "success", "message": "Success"}
        
    except Exception:
        # Ini bakal nampilin jejak error lengkap
        error_msg = traceback.format_exc()
        print(f"--- [CRITICAL ERROR TRACEBACK] ---\n{error_msg}", flush=True)
        return {"status": "error", "message": error_msg}

runpod.serverless.start({"handler": handler})