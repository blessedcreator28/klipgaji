import runpod
import os
import sys
import boto3
from faster_whisper import WhisperModel

print("LOG: Init Model...")
model = WhisperModel("small", device="cuda", compute_type="float16")

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ.get("R2_ENDPOINT_URL"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="auto"
)

def handler(event):
    print("--- LOG: HANDLER V22 START ---")
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    bucket_name = os.environ.get("R2_BUCKET_NAME")
    
    local_path = f"/tmp/{os.path.basename(s3_key)}"
    
    print(f"LOG: Downloading {s3_key}...")
    s3.download_file(bucket_name, s3_key, local_path)
    
    print(f"LOG: Transcribing...")
    segments, _ = model.transcribe(local_path, beam_size=5)
    transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    
    if os.path.exists(local_path): os.remove(local_path)
    return {"status": "success", "transcription": transcription}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})