import runpod
import os
import sys
import boto3
from faster_whisper import WhisperModel

# Load model di luar handler (init sekali saja)
model = WhisperModel("small", device="cuda", compute_type="float16")
s3 = boto3.client('s3')

sys.stdout.reconfigure(line_buffering=True)

def handler(event):
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    bucket_name = "klipgaji-bucket" # GANTI INI
    
    if not s3_key:
        return {"status": "error", "message": "s3_key missing"}
    
    local_path = f"/tmp/{os.path.basename(s3_key)}"
    
    # 1. Download dari S3
    print(f"LOG: Downloading {s3_key}...")
    s3.download_file(bucket_name, s3_key, local_path)
    
    # 2. Transkripsi
    print(f"LOG: Transcribing...")
    segments, _ = model.transcribe(local_path, beam_size=5)
    
    transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    
    # 3. Cleanup (Penting biar storage gak penuh)
    if os.path.exists(local_path):
        os.remove(local_path)
        
    return {"status": "success", "transcription": transcription}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})