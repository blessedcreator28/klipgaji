import runpod
import os
import sys
import boto3
import subprocess
import traceback
# INI YANG KETINGGALAN:
from faster_whisper import WhisperModel

# Konfigurasi log
sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

# Load model dari folder lokal yang sudah kita siapkan
print("--- [MODEL] LOADING LOCAL WHISPER MODEL ---", flush=True)
try:
    model = WhisperModel("/app/whisper-model", device="cuda", compute_type="float16")
    print("--- [MODEL] LOADED ---", flush=True)
except Exception as e:
    print(f"--- [CRITICAL] FAILED TO LOAD MODEL: {str(e)} ---", flush=True)

def handler(job):
    print(f"--- [HANDLER] JOB RECEIVED ---", flush=True)
    
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
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        # 2. FFMPEG
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        # 3. WHISPER TRANSCRIPTION
        print("--- [WHISPER] START TRANSCRIBING ---", flush=True)
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        full_text = " ".join([segment.text for segment in segments])
        
        return {"status": "success", "transcript": full_text}
        
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"--- [CRITICAL ERROR] ---\n{error_msg}", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})