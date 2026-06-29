import runpod
import os
import sys
import boto3
from faster_whisper import WhisperModel

# Load model di luar handler (init sekali saja)
print("LOG: Loading Whisper Model...")
model = WhisperModel("small", device="cuda", compute_type="float16")

# Inisialisasi S3 client untuk R2
s3 = boto3.client(
    "s3",
    endpoint_url=os.environ.get(https://df3050e61e1819164a9f528c7eddaa86.r2.cloudflarestorage.com),
    aws_access_key_id=os.environ.get(b33eb75134afc31f82a16aac4dbee7d6),
    aws_secret_access_key=os.environ.get(3b643d675df524f4ca2595c1a5df87876774646ea96a6589b36a836700bb9f04),
    region_name="auto" # R2 butuh ini
)

sys.stdout.reconfigure(line_buffering=True)

def handler(event):
    print("--- LOG: HANDLER V21 PROSES AI R2 ---")
    
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    bucket_name = os.environ.get(klipgaji-bucket)
    
    if not s3_key or not bucket_name:
        return {"status": "error", "message": "s3_key or R2_BUCKET_NAME missing"}
    
    local_path = f"/tmp/{os.path.basename(s3_key)}"
    
    # 1. Download dari R2
    print(f"LOG: Downloading {s3_key} from R2...")
    s3.download_file(bucket_name, s3_key, local_path)
    
    # 2. Transkripsi
    print(f"LOG: Transcribing...")
    segments, _ = model.transcribe(local_path, beam_size=5)
    
    transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    
    # 3. Cleanup
    if os.path.exists(local_path):
        os.remove(local_path)
        
    return {"status": "success", "transcription": transcription}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})