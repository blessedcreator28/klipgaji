import runpod
import sys

# Flush log biar muncul
sys.stdout.reconfigure(line_buffering=True)
print("--- [DEBUG] PYTHON SCRIPT BERHASIL JALAN ---", flush=True)

def handler(job):
    print("--- [DEBUG] HANDLER DIPANGGIL ---", flush=True)
    return {"status": "success", "message": "OK"}

runpod.serverless.start({"handler": handler})