import runpod
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def handler(event):
    print("--- HANDLER V20 STARTED ---")
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    
    if not s3_key:
        return {"status": "error", "message": "s3_key missing"}
    
    print(f"DEBUG: Processing {s3_key}")
    return {"status": "success", "message": "Handler V20 Active"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})