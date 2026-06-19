import runpod

def handler(event):
    return {"status": "success", "message": "Aplikasi jalan!"}

runpod.serverless.start({"handler": handler})