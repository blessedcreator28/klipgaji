import runpod
import os
import requests
import uuid
import traceback
import subprocess
import random

def format_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t % 1) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

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
        srt_path = f"/tmp/subs_{unique_id}.srt"
        output_filename = f"final_{unique_id}.mp4"
        output_path = f"/tmp/{output_filename}"

        # --- DOWNLOAD THE BOLD FONT ---
        font_url = "https://raw.githubusercontent.com/LonamiWebs/8-Bally-Pool/master/src/Resources/Original/font/theboldfont.ttf"
        font_path = "/tmp/theboldfont.ttf"
        
        if not os.path.exists(font_path):
            r_font = requests.get(font_url, stream=True)
            with open(font_path, 'wb') as f:
                for chunk in r_font.iter_content(chunk_size=8192):
                    f.write(chunk)

        # 1. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Transcribe
        result = model.transcribe(video_path, language="id", word_timestamps=True, fp16=False)
        
        target_dur = random.randint(30, 60)
        start_time = 15.0
        end_time = start_time + target_dur
        
        # 3. Merakit File SRT Dinamis Per Kata
        srt_content = ""
        sub_index = 1
        
        for seg in result.get("segments", []):
            words = seg.get("words", [])
            
            # Fallback jika timestamp kosong
            if not words:
                text = seg.get("text", "").strip()
                word_list = text.split()
                if word_list:
                    duration = seg["end"] - seg["start"]
                    t_per_word = duration / len(word_list)
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
                            srt_content += f"{sub_index}\n"
                            srt_content += f"{format_time(rel_start)} --> {format_time(rel_end)}\n"
                            srt_content += f"{clean_word}\n\n"
                            sub_index += 1

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        # 4. FFMPEG dengan Subtitles dan fontsdir (SUPER CEPAT)
        # FontName diarahkan langsung ke internal nama font tersebut
        style = "FontName=The Bold Font,FontSize=110,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=5,Shadow=0,Alignment=2,MarginV=350"
        
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10[bg];"
            "[0:v]scale=1080:-2[fg];"
            "[bg][fg]overlay=0:(H-h)/2[merged];"
            f"[merged]subtitles='{srt_path}':fontsdir='/tmp':force_style='{style}'"
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

        # 5. Upload & Cleanup
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