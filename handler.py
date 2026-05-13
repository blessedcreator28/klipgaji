import runpod
import os
import json
import requests
import whisper
import google.generativeai as genai
import subprocess
from apify_client import ApifyClient

# --- CONFIG ---
GEMINI_API_KEY = "AIzaSyDjtgJ_mcGCHnaNge9_IQ-T4eVPa06bWsA"
APIFY_API_TOKEN = "apify_api_vdGETkyLa81szZocmE9uSqB7XryEbJ2cKusz"

def create_word_ass(start_time, end_time, segments, filename):
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,The Bold Font,75,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,0,2,10,10,500,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def format_time(seconds):
        seconds = max(0, seconds)
        h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for seg in segments:
            if 'words' in seg:
                for word in seg['words']:
                    if word['end'] > start_time and word['start'] < end_time:
                        rel_start = max(0, word['start'] - start_time)
                        rel_end = min(end_time - start_time, word['end'] - start_time)
                        clean_word = word['word'].strip().upper()
                        if clean_word:
                            f.write(f"Dialogue: 0,{format_time(rel_start)},{format_time(rel_end)},Default,,0,0,0,,{clean_word}\n")

def handler(job):
    try:
        job_input = job["input"]
        youtube_url = job_input.get("url")
        if not youtube_url: return {"error": "URL missing"}

        # 1. APIFY DOWNLOAD
        client = ApifyClient(APIFY_API_TOKEN)
        run = client.actor("streamers/youtube-video-downloader").call(run_input={"videos": [{"url": youtube_url}]})
        item = client.dataset(run["defaultDatasetId"]).list_items().items[0]
        video_url = item.get('downloadedFileUrl') or item.get('audioOnlyUrl')

        raw_path = "/tmp/video.mp4"
        audio_path = "/tmp/audio.m4a"
        
        with requests.get(video_url, stream=True) as r:
            with open(raw_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        subprocess.run(["ffmpeg", "-y", "-i", raw_path, "-vn", "-acodec", "aac", audio_path], check=True)

        # 2. WHISPER
        model = whisper.load_model("small")
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        
        # 3. GEMINI
        genai.configure(api_key=GEMINI_API_KEY)
        model_gemini = genai.GenerativeModel('models/gemini-2.5-flash')
        transcript = "".join([f"[{s['start']}s]: {s['text']}\n" for s in result['segments']])
        response = model_gemini.generate_content(f"Pilih 10 momen viral. Return JSON array [{{'start': 10, 'end': 40}}]. Transcript: {transcript[:15000]}")
        moments = json.loads(response.text.replace('```json', '').replace('```', '').strip())

        # 4. RENDER (CPU MODE)
        output_files = []
        for i, m in enumerate(moments):
            out = f"/tmp/hasil_{i}.mp4"
            ass = f"/tmp/sub_{i}.ass"
            create_word_ass(m['start'], m['end'], result['segments'], ass)
            
            cmd = [
                "ffmpeg", "-y", "-ss", str(m['start']), "-t", str(m['end']-m['start']),
                "-i", raw_path,
                "-filter_complex", f"[0:v]split=2[bg_in][fg_in];[bg_in]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=20[bg];[fg_in]scale=720:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles={ass}",
                "-c:v", "libx264", "-preset", "ultrafast", out
            ]
            subprocess.run(cmd, check=True)
            output_files.append(out)

        return {"status": "success", "files": output_files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})