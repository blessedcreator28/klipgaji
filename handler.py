import runpod
import os
import boto3
import sys
import subprocess
from faster_whisper import WhisperModel

# Konfigurasi log
sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

# Load model di awal (global) supaya request berikutnya instan
print("--- [MODEL] LOADING WHISPER MODEL ---", flush=True)
model = WhisperModel("base", device="cuda", compute_type="float16")
print("--- [MODEL] LOADED ---", flush=True)

def handler(job):
    print(f"--- [HANDLER] JOB RECEIVED: {job.get('id')} ---", flush=True)
    
    try:
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
        
        # Gabungin teksnya
        full_text = []
        for segment in segments:
            full_text.append(segment.text)
        
        result_text = " ".join(full_text)
        print(f"--- [WHISPER] SUCCESS: {len(result_text)} chars transcribed ---", flush=True)
        
        return {"status": "success", "transcript": result_text}
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR] {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})