import runpod
import os
import requests
import uuid
import traceback

def handler(job):
    try:
        # 1. Pindahkan import ke dalam supaya worker bisa nyala dulu
        import whisper
        from supabase import create_client
        
        # 2. Cek Environment Variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            return {"status": "error", "message": "SUPABASE_URL / KEY tidak ada di Environment RunPod!"}

        # 3. Inisialisasi
        supabase = create_client(supabase_url, supabase_key)
        model = whisper.load_model("base")

        # 4. Ambil Link Video
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        
        if not video_url:
            return {"status": "error", "message": "No video_url provided"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/video_{unique_id}.mp4"

        # 5. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 6. Transcribe
        result = model.transcribe(video_path, word_timestamps=True)
        
        return {
            "status": "success", 
            "urls": [video_url],
            "transcription": result['text'][:100]
        }

    except Exception as e:
        # Kalau ada error, mesin ga akan mati, tapi ngirim errornya ke Streamlit lo
        return {
            "status": "error", 
            "message": str(e), 
            "traceback": traceback.format_exc()
        }

runpod.serverless.start({"handler": handler})
