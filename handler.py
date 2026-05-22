import runpod
import os
import requests
import uuid
import traceback
import subprocess
import random

def handler(job):
    try:
        import whisper
        from supabase import create_client
        
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"

        supabase = create_client(supabase_url, supabase_key)
        model = whisper.load_model("small")

        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        
        if not video_url:
            return {"status": "error", "message": "No video_url provided"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        
        # --- PREPARE FONT ---
        font_url = "https://raw.githubusercontent.com/LonamiWebs/8-Bally-Pool/master/src/Resources/Original/font/theboldfont.ttf"
        font_path = "/tmp/theboldfont.ttf"
        
        # Fake User-Agent biar gak ditendang server saat download
        fake_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        if not os.path.exists(font_path):
            r_font = requests.get(font_url, stream=True, headers=fake_headers)
            with open(font_path, 'wb') as f:
                for chunk in r_font.iter_content(chunk_size=8192):
                    f.write(chunk)

        # 1. Download Video Mentah (Pakai Topeng Anti-Blokir Catbox)
        r = requests.get(video_url, stream=True, headers=fake_headers)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Transcribe Total
        result = model.transcribe(video_path, language="id", word_timestamps=True, fp16=False)
        segments = result.get("segments", [])
        
        if not segments:
             return {"status": "error", "message": "Tidak ada suara yang terdeteksi di video."}
             
        total_duration = segments[-1]["end"]
        
        # --- INISIALISASI MESIN PABRIK MULTI-CLIP ---
        start_time = 15.0 
        clip_urls = []
        clip_count = 1
        max_clips = 25 
        
        while start_time < total_duration and clip_count <= max_clips:
            target_dur = random.randint(30, 60)
            end_time = start_time + target_dur
            
            if (total_duration - start_time) < 30.0:
                break
                
            if end_time > total_duration:
                end_time = total_duration
                target_dur = end_time - start_time

            output_filename = f"clip_{clip_count}_{unique_id}.mp4"
            output_path = f"/tmp/{output_filename}"
            
            drawtexts = []
            for seg in segments:
                words = seg.get("words", [])
                
                if not words:
                    text = seg.get("text", "").strip()
                    word_list = text.split()
                    if word_list:
                        seg_dur = seg["end"] - seg["start"]
                        t_per_word = seg_dur / len(word_list)
                        for i, w in enumerate(word_list):
                            words.append({
                                "word": w,
                                "start": seg["start"] + (i * t_per_word),
                                "end": seg["start"] + ((i + 1) * t_per_word)
                            })

                for w_info in words:
                    w_start = w_info["start"]
                    w_end = w_info["end"]

                    if w_end > start_time and w_start < end_time:
                        rel_start = max(0.0, w_start - start_time)
                        rel_end = min(float(target_dur), w_end - start_time)

                        if rel_end > rel_start:
                            clean_word = "".join(c for c in w_info['word'] if c.isalnum() or c in ".,?!").upper()
                            if clean_word:
                                dt = f"drawtext=fontfile='{font_path}':text='{clean_word}':fontcolor=yellow:fontsize=120:borderw=8:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2+350:enable='between(t,{rel_start},{rel_end})'"
                                drawtexts.append(dt)

            base_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2"
            
            if drawtexts:
                dt_chain = ",".join(drawtexts)
                filter_complex = f"{base_filter}[merged];[merged]{dt_chain}"
            else:
                filter_complex = base_filter

            ffmpeg_cmd = [
                "ffmpeg", "-y", 
                "-ss", str(start_time), "-t", str(target_dur), 
                "-i", video_path,
                "-filter_complex", filter_complex,
                "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", 
                output_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            with open(output_path, "rb") as f:
                supabase.storage.from_("videos").upload(path=output_filename, file=f)
            
            clip_url = supabase.storage.from_("videos").get_public_url(output_filename)
            clip_urls.append(clip_url)
            
            os.remove(output_path)
            
            start_time = end_time
            clip_count += 1

        if os.path.exists(video_path):
            os.remove(video_path)

        return {
            "status": "success", 
            "urls": clip_urls,
            "total_clips": len(clip_urls)
        }

    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})