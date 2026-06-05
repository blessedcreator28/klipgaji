import runpod
import sys

# Konfigurasi log
sys.stdout.reconfigure(line_buffering=True)
print("--- [TEST] SCRIPT BOOTING ---", flush=True)

def handler(job):
    print("--- [TEST] HANDLER CALLED ---", flush=True)
    return {"status": "success", "message": "Test successful"}

runpod.serverless.start({"handler": handler})q