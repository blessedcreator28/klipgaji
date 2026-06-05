import runpod

print("--- [BOOT TEST] SCRIPT BERHASIL DIMUAT ---", flush=True)

def handler(job):
    print("--- [HANDLER] FUNGSI DIPANGGIL ---", flush=True)
    return {"status": "success", "message": "Test successful"}

runpod.serverless.start({"handler": handler})