import runpod
import os
import sys
import boto3
import traceback

# Setup system
sys.stdout.reconfigure(line_buffering=True)

def handler(event):
    print("--- LOG: HANDLER V21 STARTUP ---")
    try:
        # Import di dalam handler biar tidak langsung crash saat startup
        from faster_whisper import WhisperModel
        
        # Inisialisasi Model
        print("LOG: Loading Model...")
        model = WhisperModel("small", device="cuda", compute_type="float16")
        
        # Logika S3
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ.get("R2_ENDPOINT_URL"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name="auto"
        )
        
        print("LOG: Handler Berhasil Inisialisasi")
        return {"status": "success", "message": "Backend Ready"}

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})