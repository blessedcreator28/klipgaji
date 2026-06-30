import os
import re
import boto3
import runpod
from faster_whisper import WhisperModel

# Import fungsi otak AI yang baru saja lo buat
from analyzer import analyze_transcription 

# Load Credential R2
ENDPOINT_URL = os.environ.get("R2_ENDPOINT")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.environ.get("R2_BUCKET")

print("LOG: Loading Model Whisper...")
model = WhisperModel("small", device="cuda", compute_type="float16")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

def handler(event):
    print("--- LOG: HANDLER V27 (WHISPER + GEMINI) ---")
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")

    if not s3_key:
        return {"status": "error", "message": "s3_key missing"}

    clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', s3_key)
    local_path = f"/tmp/{clean_name}"

    print(f"LOG: Downloading {s3_key} from R2...")
    s3.download_file(BUCKET_NAME, s3_key, local_path)

    print(f"LOG: Transcribing Video...")
    segments, _ = model.transcribe(local_path, beam_size=5)
    transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]

    # --- PROSES ANALISIS VIRAL ---
    print("LOG: Menganalisis momen viral dengan Gemini 2.5 Flash...")
    try:
        # Mengirim hasil transkripsi ke Gemini
        viral_clips_data = analyze_transcription(transcription)
    except Exception as e:
        print(f"LOG: Error pada Gemini - {e}")
        viral_clips_data = {"error": str(e)}

    # Cleanup file lokal RunPod
    if os.path.exists(local_path): 
        os.remove(local_path)

    # Mengembalikan output komplit
    return {
        "status": "success", 
        "transcription": transcription,
        "viral_clips": viral_clips_data
    }

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})