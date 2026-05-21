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

        # 2. Transcribe
        result = model.transcribe(video_path)
        segments = result.get("segments", [])
        
        # --- LOGIKA BARU: BLINDFOLD INTRO ---
        # Kata-kata provokatif tapi profesional untuk nangkep audiens lokal
        hook_keywords = [
            "rahasia", "bongkar", "fatal", "strategi", "terbukti", 
            "jangan sampai", "alasan", "kenapa", "fakta", "bayangin", 
            "perhatikan", "dengerin", "stop"
        ]
        
        start_index = 0
        start_time = 0.0
        end_time = 0.0
        clip_text = ""

        if segments:
            # 1. Paksa lewati 15 detik pertama (Biar thumbnail/intro ke-skip)
            for i, seg in enumerate(segments):
                if seg["start"] >= 15.0:
                    text_lower = seg["text"].lower()
                    # 2. Baru cari hook viral setelah intro lewat
                    if any(kw in text_lower for kw in hook_keywords):
                        start_index = i
                        break
            
            # 3. Kalau udah dilewati 15 detik tapi ga ada kata hook satupun, 
            # potong paksa persis dari detik ke-15 aja.
            if start_index == 0:
                for i, seg in enumerate(segments):
                    if seg["start"] >= 15.0:
                        start_index = i
                        break

            # Mulai merangkai klip
            current_start = segments[start_index]["start"]
            for seg in segments[start_index:]:
                clip_text += seg["text"] + " "
                duration = seg["end"] - current_start
                
                if duration >= 30:
                    end_time = seg["end"]
                    start_time = current_start
                    break
            
            if end_time == 0.0:
                start_time = segments[start_index]["start"]
                end_time = segments[-1]["end"]
        else:
            end_time = 30.0

        duration_to_cut = end_time - start_time
        
        # 4. Potong pakai FFmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", video_path, 
            "-ss", str(start_time), "-t", str(duration_to_cut), 
            "-c:v", "libx264", "-c:a", "aac", output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 5. Upload Hasil ke Supabase
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