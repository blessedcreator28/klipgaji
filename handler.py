import runpod

def handler(job):
    job_input = job['input']
    video_url = job_input.get("video_url", "Tidak ada URL")
    
    print(f"Memproses video: {video_url}")
    
    # Ini yang bikin server ngasih jawaban balik (nggak None lagi)
    return {
        "status": "success",
        "message": "Video berhasil diproses di awan!",
        "download_url": "https://hasil-video.com/jagoan-clipper.mp4"
    }

# Menjalankan worker RunPod
runpod.serverless.start({"handler": handler})
