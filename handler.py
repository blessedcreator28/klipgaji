import runpod
import os

def handler(event):
    # Debug: Print lokasi file saat ini agar kita tahu skrip mana yang jalan
    print(f"DEBUG: CURRENT FILE PATH: {__file__}")
    
    # Cek isi folder /app atau / (root)
    content = os.listdir('/')
    print(f"DEBUG: ROOT DIRECTORY CONTENT: {content}")
    
    return {
        "status": "success",
        "message": "Script is live!",
        "file_path": __file__
    }

runpod.serverless.start({"handler": handler})