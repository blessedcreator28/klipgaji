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
        if not video_url: return {"status": "error", "message": "No video_url"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        font_path = "/tmp/theboldfont.ttf"
        
        # Download Font
        if not os.path.exists(font_path):
            r_font = requests.get("https://raw.githubusercontent.com/LonamiWebs/8-Bally-Pool/master/src/Resources/Original/font/theboldfont.ttf", stream=True)
            with open(font_path, 'wb') as f:
                for chunk in r_font.iter_content(chunk_size=8192): f.write(chunk)

        # Download Video
        r = requests.get(video_url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        result = model.transcribe(video_path, language="id", word_timestamps=True, fp16=False)
        segments = result.get("segments", [])
        total_duration = segments[-1]["end"] if segments else 60
        
        # --- STRATEGI PANEN AGRESIF ---
        start_time = 15.0 
        clip_urls = []
        clip_count = 1
        max_clips = 100 # Kita buka limit sampai 100
        
        # Geser jendela potong lebih rapat (setiap 20 detik)
        while start_time < total_duration and clip_count <= max_clips:
            # Durasi 15-30 detik biar konten padat
            target_dur = random.randint(15, 30) 
            end_time = start_time + target_dur
            
            if (total_duration - start_time) < 10.0: break
            if end_time > total_duration: end_time = total_duration

            output_path = f"/tmp/clip_{clip_count}.mp4"
            
            # Drawtext dinamis
            drawtexts = []
            for seg in segments:
                for w_info in seg.get("words", []):
                    if w_info["end"] > start_time and w_info["start"] < end_time:
                        rel_start = max(0.0, w_info["start"] - start_time)
                        rel_end = min(float(target_dur), w_info["end"] - start_time)
                        clean_word = "".join(c for c in w_info['word'] if c.isalnum() or c in ".,?!").upper()
                        if clean_word:
                            drawtexts.append(f"drawtext=fontfile='{font_path}':text='{clean_word}':fontcolor=yellow:fontsize=120:borderw=8:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2+350:enable='between(t,{rel_start},{rel_end})'")

            # Filter visual
            base_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2"
            filter_complex = f"{base_filter}[merged];[merged]{','.join(drawtexts)}" if drawtexts else base_filter

            ffmpeg_cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(target_dur), "-i", video_path, "-filter_complex", filter_complex, "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", output_path]
            subprocess.run(ffmpeg_cmd, check=True)

            with open(output_path, "rb") as f:
                supabase.storage.from_("videos").upload(path=f"clip_{unique_id}_{clip_count}.mp4", file=f)
            
            clip_urls.append(supabase.storage.from_("videos").get_public_url(f"clip_{unique_id}_{clip_count}.mp4"))
            os.remove(output_path)
            
            # Geser start_time lebih rapat untuk panen lebih banyak
            start_time += 20.0 
            clip_count += 1

        if os.path.exists(video_path): os.remove(video_path)
        return {"status": "success", "urls": clip_urls, "total_clips": len(clip_urls)}

    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})