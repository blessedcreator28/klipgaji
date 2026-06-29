import runpod
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def handler(event):
    print("--- LOG: HANDLER V21 AKTIF ---")
    
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    
    if not s3_key:
        print("LOG: ERROR - s3_key tidak ditemukan!")
        return {"status": "error", "message": "s3_key missing"}
    
    print(f"LOG: Berhasil memproses key: {s3_key}")
    return {"status": "success", "message": "Handler V21 Berjalan Lancar"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})