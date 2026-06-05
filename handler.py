import runpod
import os
import sys
import boto3
import subprocess
import traceback

# Konfigurasi log
sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

def handler(job):
    print(f"--- [HANDLER] JOB RECEIVED ---", flush=True)
    
    try:
        # Import di dalam sini supaya kalau error, kita bisa nangkep pesannya
        print("--- [DEBUG] ATTEMPTING IMPORT ---", flush=True)
        from faster_whisper import WhisperModel
        print("--- [DEBUG] IMPORT SUCCESS ---", flush=True)
        
        # Load model
        model = WhisperModel("base", device="cuda", compute_type="float16")
        
        # ... (sisa logika download & ffmpeg tetep ada, tapi ini buat ngetes import dulu)
        return {"status": "success", "message": "Import success, model loaded"}
        
    except Exception:
        # Ini bakal nampilin error asli kenapa dia crash
        error_msg = traceback.format_exc()
        print(f"--- [CRITICAL IMPORT ERROR] ---\n{error_msg}", flush=True)
        return {"status": "error", "message": error_msg}

runpod.serverless.start({"handler": handler})