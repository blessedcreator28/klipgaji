import os
import json
from google import genai
from google.genai import types

# Inisialisasi Client
# Menggunakan GOOGLE_API_KEY (sesuai settingan RunPod terakhir) atau fallback ke GEMINI_API_KEY
API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Error: API Key tidak ditemukan!")

client = genai.Client(api_key=API_KEY)

def analyze_transcription(transcription_data):
    formatted_transcription = ""
    for segment in transcription_data:
        formatted_transcription += f"[{segment['start']} - {segment['end']}] {segment['text']}\n"
        
    system_instruction = """
    Lo adalah Editor Video Senior dan Pakar Viral Marketing. 
    Analisis transkripsi dan cari segmen viral (15-60 detik).
    Output WAJIB JSON dengan format:
    {"clips": [{"title": "str", "start_time": float, "end_time": float, "reason": "str"}]}
    """

    print("LOG: Mengirim transkripsi ke Gemini 1.5 Flash...")
    
    # PERUBAHAN: Downgrade ke 1.5 Flash agar aman dari limit free tier
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=f"Transkripsi:\n{formatted_transcription}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
        ),
    )
    
    return json.loads(response.text)

if __name__ == "__main__":
    sample_transcription = [
        {"start": 0.0, "end": 5.88, "text": "Jadi gini, cara kerja otak itu adalah mereka hanya akan mengingat sesuatu yang menurut mereka penting."},
        {"start": 5.88, "end": 12.08, "text": "Ketika mereka belajar, tapi tidak dikasih tahu maknanya apa, mereka nggak tahu suka saya belajar ini vaidahnya untuk apa."},
        {"start": 12.08, "end": 16.96, "text": "Maka si otak itu akan mencoba menghapus materi yang kita belajari."},
        {"start": 16.96, "end": 20.48, "text": "Terus sama kita diingat-ingat lagi, karena harus ulangan."},
        {"start": 20.48, "end": 24.76, "text": "Terus sama otak secara otomatis dihapus lagi, diingat lagi, dihapus lagi."},
        {"start": 24.76, "end": 28.76, "text": "Itulah yang terjadi waktu kita sekolah, dan betapa merusaknya itu terhadap otak."},
        {"start": 28.76, "end": 33.68, "text": "Karena otak dipaksa untuk mengingat sesuatu yang dia tidak tahu maknanya apa."}
    ]
    
    try:
        result = analyze_transcription(sample_transcription)
        print("\n--- HASIL ANALISIS GEMINI ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\nLOG: Error: {e}")