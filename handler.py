import runpod
import sys

print("--- [DIAGNOSTIC] SCRIPT STARTING ---", flush=True)

def handler(job):
    print("--- [DIAGNOSTIC] HANDLER RUNNING ---", flush=True)
    return {"status": "success", "message": "Standard Python Container is Alive"}

runpod.serverless.start({"handler": handler})