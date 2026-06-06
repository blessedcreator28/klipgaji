import runpod
import boto3
import subprocess
import sys

sys.stdout.reconfigure(line_buffering=True)
print("--- [DIAGNOSTIC] STARTING ---", flush=True)

def handler(job):
    print("--- [DIAGNOSTIC] RUNNING BOTO3 & FFMPEG TEST ---", flush=True)
    
    # 1. Test Boto3
    try:
        boto3.client('s3')
        print("--- [PASS] Boto3 Loaded ---", flush=True)
    except Exception as e:
        return {"status": "error", "message": f"Boto3 fail: {str(e)}"}
        
    # 2. Test FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
        print("--- [PASS] FFmpeg Loaded ---", flush=True)
    except Exception as e:
        return {"status": "error", "message": f"FFmpeg fail: {str(e)}"}

    return {"status": "success", "message": "Environment Setup Verified"}

runpod.serverless.start({"handler": handler})