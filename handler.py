import runpod
import os
import sys

# Kita pake print yang paling basic
print("--- [DEBUG] STARTING SCRIPT ---", flush=True)

def handler(job):
    print("--- [DEBUG] HANDLER STARTED ---", flush=True)
    
    # IMPORT DI DALAM SINI (Biar gak crash di awal)
    try:
        print("--- [DEBUG] IMPORTING LIBRARIES ---", flush=True)
        import boto3
        import subprocess
        from faster_whisper import WhisperModel
        print("--- [DEBUG] IMPORTS SUCCESS ---", flush=True)
        
        print("--- [DEBUG] LOADING MODEL ---", flush=True)
        model = WhisperModel("/app/whisper-model", device="cuda", compute_type="float16")
        print("--- [DEBUG] MODEL LOADED ---", flush=True)
    except Exception as e:
        print(f"--- [CRITICAL ERROR DURING INIT] {str(e)} ---", flush=True)
        return {"status": "error", "message": f"Init failed: {str(e)}"}

    try:
        # Sisanya logika download & proses
        print("--- [DEBUG] DOWNLOADING ---", flush=True)
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
        
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        print("--- [DEBUG] TRANSCRIBING ---", flush=True)
        segments, info = model.transcribe(audio_path, beam_size=5)
        full_text = " ".join([segment.text for segment in segments])
        
        return {"status": "success", "transcript": full_text}
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR DURING RUN] {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})