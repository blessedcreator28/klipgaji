cat <<EOF > handler.py
import sys
# Flush log supaya kita bisa baca
sys.stdout.reconfigure(line_buffering=True)
print("--- [DIAGNOSTIC] SCRIPT STARTING ---", flush=True)

try:
    import torch
    print(f"--- [DIAGNOSTIC] Torch available: {torch.cuda.is_available()} ---", flush=True)
    from faster_whisper import WhisperModel
    print("--- [DIAGNOSTIC] Imports Success ---", flush=True)
    
    # KITA PAKSA CPU DULU BUAT TES
    print("--- [DIAGNOSTIC] Loading Model on CPU ---", flush=True)
    model = WhisperModel("/app/whisper-model", device="cpu", compute_type="int8")
    print("--- [DIAGNOSTIC] Model Loaded on CPU ---", flush=True)

except Exception as e:
    print(f"--- [DIAGNOSTIC CRASH] {str(e)} ---", flush=True)
    sys.exit(1)

import runpod
def handler(job):
    return {"status": "success", "message": "CPU Test Passed"}

runpod.serverless.start({"handler": handler})
EOF