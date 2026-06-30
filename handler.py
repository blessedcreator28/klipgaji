import runpod
import os
import boto3
import re
from faster_whisper import WhisperModel

# 1. Konfigurasi Hardcoded (Anti-Cache)
ENDPOINT_URL = "https://df3050e61e1819164a9f528c7eddaa86.r2.cloudflarestorage.com"
ACCESS_KEY = "b33eb75134afc31f82a16aac4dbee7d6"
SECRET_KEY = "3b643d675df524f4ca2595c1a5df87876774646ea96a6589b36a836700bb9f04"
BUCKET_NAME = "klipgaji-bucket"

# 2. Inisialisasi Model & S3
print("LOG: Loading Model...")
model = WhisperModel("small", device="cuda", compute_type="float16")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

def handler(event):
    print("--- LOG: HANDLER V25 PROSES AI ---")
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    
    if not s3_key:
        return {"status": "error", "message": "s3_key missing"}
    
    # 3. Sanitasi Nama File
    clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', s3_key)
    local_path = f"/tmp/{clean_name}"
    
    # 4. Download dari R2
    print(f"LOG: Downloading {s3_key}...")
    s3.download_file(BUCKET_NAME, s3_key, local_path)
    
    # 5. Transkripsi
    print(f"LOG: Transcribing...")
    segments, _ = model.transcribe(local_path, beam_size=5)
    transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    
    # 6. Cleanup
    if os.path.exists(local_path): os.remove(local_path)
    
    return {"status": "success", "transcription": transcription}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})