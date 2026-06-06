import runpod
import sys

# Flush log biar muncul
sys.stdout.reconfigure(line_buffering=True)
print("--- [DIAGNOSTIC] SCRIPT STARTING ---", flush=True)

def handler(job):
    print("--- [DIAGNOSTIC] HANDLER RUNNING ---", flush=True)
    return {"status": "success", "message": "Container is alive"}

# Ini cara standar runpod
runpod.serverless.start({"handler": handler})