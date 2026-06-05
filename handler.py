import runpod
import sys

# Konfigurasi log paling dasar
sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

def handler(job):
    print("--- [HANDLER] JOB RECEIVED ---", flush=True)
    return {"status": "success", "message": "Handler is working"}

runpod.serverless.start({"handler": handler})