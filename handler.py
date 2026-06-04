import runpod
import os
import requests
import uuid
import traceback
import subprocess
import whisper
from supabase import create_client

model = whisper.load_model("tiny") 

def generate_mrbeast_subs(words, clip_start, ass_path):
    # Racikan rahasia: Subtitle ASS gaya MrBeast (Word-by-word, Kuning, Outline Hitam Tebal, Posisi Tengah)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MrBeast,Arial,130,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,5,2,10,10,800,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    def format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:01d}:{m:02d}:{s:05.2f}"
        
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for w in words:
            start_t = max(0, w['start'] - clip_start)
            end_t = max(0, w['end'] - clip_start)
            if end_t <= 0: continue
            
            t_start = format_time(start_t)
            t_end = format_time(end_t)
            # Bersihkan tanda baca dan jadikan HURUF KAPITAL semua
            text = w['word'].strip().upper()
            
            f.write(f"Dialogue: 0,{t_start},{t_end},MrBeast,,0,0,0,,{text}\n")


def handler(job):
    try:
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
        
        supabase = create_client(supabase_url, supabase_key)
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        
        if not video_url: return {"status": "error", "message": "No video_url"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(video_url, stream=True, headers=headers)
        r.raise_for_status() 
        
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                
        # AI MENDENGAR SECARA DETAIL (Word Timestamps)
        result = model.transcribe(video_path, language="id", word_timestamps=True)
        segments = result.get("segments", [])
        
        # LOGIKA PEMOTONGAN CERDAS BERDASARKAN KONTEKS (Target: 40-60 detik)
        clips = []
        current_clip = {"start": 0, "end": 0, "words": []}
        
        for seg in segments:
            if not current_clip["words"]:
                current_clip["start"] = seg["start"]
                
            if "words" in seg:
                current_clip["words"].extend(seg["words"])
                
            current_clip["end"] = seg["end"]
            duration = current_clip["end"] - current_clip["start"]
            
            # Jika durasi sudah mencukupi (>= 40 detik), potong di akhir kalimat ini
            if duration >= 40.0:
                clips.append(current_clip)
                current_clip = {"start": 0, "end": 0, "words": []}
                # Batasi maksimal 3 klip daging per eksekusi agar render cepat
                if len(clips) >= 3: break 
                
        # Ambil sisa percakapan jika durasinya lebih dari 20 detik
        if current_clip["words"] and (current_clip["end"] - current_clip["start"] >= 20.0) and len(clips) < 3:
            clips.append(current_clip)

        clip_urls = []
        
        # PROSES RENDER (POTONG + BLUR + MRBEAST TEXT)
        for i, c in enumerate(clips):
            clip_start = c["start"]
            clip_end = c["end"]
            duration = clip_end - clip_start
            
            output_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            ass_path = f"/tmp/subs_{unique_id}_{i}.ass"
            
            generate_mrbeast_subs(c["words"], clip_start, ass_path)
            
            safe_ass = ass_path.replace(":", "\\\\:")
            
            complex_filter = f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v_overlay];[v_overlay]subtitles='{safe_ass}'"
            
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-ss", str(clip_start), "-t", str(duration), 
                "-i", video_path, 
                "-filter_complex", complex_filter, 
                "-c:v", "libx264", "-c:a", "aac", output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True)

            with open(output_path, "rb") as f:
                supabase.storage.from_("videos").upload(path=f"clip_{unique_id}_{i}.mp4", file=f)
            
            clip_urls.append(supabase.storage.from_("videos").get_public_url(f"clip_{unique_id}_{i}.mp4"))
            
            os.remove(output_path)
            os.remove(ass_path)

        if os.path.exists(video_path): os.remove(video_path)
        return {"status": "success", "urls": clip_urls}

    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})