import runpod
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def handler(event):
    print("--- HANDLER STARTED ---")
    
    # Ambil input dengan aman
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    
    if not s3_key:
        print("ERROR: s3_key is missing in input!")
        return {"status": "error", "message": "s3_key is missing"}
    
    print(f"DEBUG: Processing key: {s3_key}")
    
    # Lanjut logika berikutnya...
    return {
        "status": "success", 
        "message": "Input received successfully",
        "received_key": s3_key
    }

runpod.serverless.start({"handler": handler})