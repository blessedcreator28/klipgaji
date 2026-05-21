import runpod
import os
import requests
import uuid
import traceback
import subprocess
import random

def format_time(t):
    # Mengubah detik jadi format waktu SRT
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t % 1) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def handler(job):
    try:
        import whisper
        from supabase import create_client
        
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"

        supabase = create_client(supabase_url, supabase_key)
        
        # 1. UPGRADE MODEL KE 'small' BIAR BAHASA INDONESIA TAJAM & GAK HALUSINASI
        model = whisper.load_model("small")

        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        
        if not video_url:
            return {"status": "error", "message": "No video_url provided"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        srt_path = f"/tmp/subs_{unique_id}.srt"
        output_filename = f"final_{unique_id}.mp4"
        output_path = f"/tmp/{output_filename}"

        # 2. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. Transcribe (Tanpa word_timestamps bawaan yang cacat)
        result = model.transcribe(video_path)
        
        target_dur = random.randint(30, 60)
        start_time = 15.0
        end_time = start_time + target_dur
        
        # 4. ALGORITMA PAKSA PECAH PER KATA (MRBEAST STYLE GUARANTEED)
        srt_content = ""
        sub_index = 1
        
        for seg in result.get("segments", []):
            seg_start = seg["start"]
            seg_end = seg["end"]
            text = seg["text"].strip()
            
            # Cuma ambil suara di durasi klip kita
            if seg_end > start_time and seg_start < end_time:
                words = text.split()
                if not words:
                    continue
                    
                # Bagi durasi suara secara merata ke setiap kata
                seg_duration = seg_end - seg_start
                time_per_word = seg_duration / len(words)
                
                for i, word in enumerate(words):
                    w_start = seg_start + (i * time_per_word)
                    w_end = w_start + time_per_word
                    
                    # Relatifkan ke waktu potong video FFmpeg (-ss)
                    rel_start = max(0, w_start - start_time)
                    rel_end = min(target_dur, w_end - start_time)
                    
                    if rel_end > rel_start:
                        # Bersihkan simbol aneh supaya ga crash
                        clean_word = "".join(e for e in word if e.isalnum() or e.isspace()).upper()
                        
                        srt_content += f"{sub_index}\n"
                        srt_content += f"{format_time(rel_start)} --> {format_time(rel_end)}\n"
                        srt_content += f"{clean_word}\n\n"
                        sub_index += 1

        # Tulis ke GPU
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # 5. FFMPEG dengan Subtitles Filter
        # Font lebih besar (FontSize=100), Outline tebal
        style = "FontName=Arial,FontSize=100,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=5,Shadow=0,Alignment=2,MarginV=600"
        
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10[bg];"
            "[0:v]scale=1080:-2[fg];"
            "[bg][fg]overlay=0:(H-h)/2[merged];"
            f"[merged]subtitles='{srt_path}':force_style='{style}'"
        )
        
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-ss", str(start_time), "-t", str(target_dur), 
            "-i", video_path,
            "-filter_complex", filter_complex,
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", 
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 6. Upload Hasil ke Supabase
        with open(output_path, "rb") as f:
            supabase.storage.from_("videos").upload(path=output_filename, file=f)
        
        clip_url = supabase.storage.from_("videos").get_public_url(output_filename)

        os.remove(video_path)
        os.remove(output_path)
        os.remove(srt_path)

        return {"status": "success", "urls": [clip_url]}

    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})