import runpod
import os
import requests
import uuid
import traceback
import subprocess

def handler(job):
    try:
        import whisper
        from supabase import create_client
        
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"

        supabase = create_client(supabase_url, supabase_key)
        model = whisper.load_model("base")

        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        
        if not video_url:
            return {"status": "error", "message": "No video_url provided"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        output_filename = f"clip_{unique_id}.mp4"
        output_path = f"/tmp/{output_filename}"

        # 1. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Transcribe (AI Whisper baca teks dan waktunya)
        result = model.transcribe(video_path)
        segments = result.get("segments", [])
        
        # 3. Logika Pemotongan Cerdas (30-60 Detik, Kalimat Utuh)
        start_time = 0.0
        end_time = 0.0
        clip_text = ""
        
        if not segments:
            # Jika tidak ada suara, potong statis 30 detik
            end_time = 30.0
        else:
            current_start = segments[0]["start"]
            for seg in segments:
                clip_text += seg["text"] + " "
                duration = seg["end"] - current_start
                
                # Begitu kumpulan kalimat menyentuh angka 30 detik (tapi di bawah 60), kunci potongannya.
                if duration >= 30:
                    end_time = seg["end"]
                    start_time = current_start
                    break
                    
            # Jika video totalnya kurang dari 30 detik, ambil semuanya
            if end_time == 0.0:
                start_time = segments[0]["start"]
                end_time = segments[-1]["end"]

        duration_to_cut = end_time - start_time
        
        # 4. Potong pakai FFmpeg dengan start dan durasi dinamis
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", video_path, 
            "-ss", str(start_time), "-t", str(duration_to_cut), 
            "-c:v", "libx264", "-c:a", "aac", output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 5. Upload Hasil Potongan ke Supabase
        with open(output_path, "rb") as f:
            supabase.storage.from_("videos").upload(
                path=output_filename,
                file=f,
                file_options={"content-type": "video/mp4"}
            )
        
        clip_url = supabase.storage.from_("videos").get_public_url(output_filename)

        os.remove(video_path)
        os.remove(output_path)

        return {
            "status": "success", 
            "urls": [clip_url],
            "transcription": clip_text.strip()
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e), 
            "traceback": traceback.format_exc()
        }

runpod.serverless.start({"handler": handler})