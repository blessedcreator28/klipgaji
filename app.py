import streamlit as st
import requests
import time
from supabase import create_client

# --- CONFIG & KEYS ---
SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "mj3o3oohv9up54"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="KlipGaji - Auto Viral", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stButton>button { border: 2px solid #FF7F50; color: #FF7F50; background-color: transparent; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #FF7F50; color: white; }
</style>
""", unsafe_allow_html=True)

st.session_state.authenticated = True

st.title("🔥 KlipGaji (Dev Mode)")
st.markdown("Mesin pencetak klip otomatis untuk dominasi market lokal. Upload, tinggal tidur, panen!")

uploaded_file = st.file_uploader("Upload Video Mentah Lo Di Sini (Batas Aman: Max 200MB / ~15 Menit)", type=['mp4', 'mov'])

if uploaded_file and st.button("Proses Video"):
    with st.spinner("Mengamankan video ke brankas... (Jangan tutup halaman)"):
        file_ext = uploaded_file.name.split('.')[-1]
        unique_filename = f"input_raw_{int(time.time())}.{file_ext}"
        
        supabase.storage.from_("videos").upload(
            path=unique_filename,
            file=uploaded_file.getvalue(),
            file_options={"content-type": f"video/{file_ext}"}
        )
        public_url = supabase.storage.from_("videos").get_public_url(unique_filename)
    
    with st.spinner("Mengirim perintah eksekusi ke AI..."):
        runpod_resp = requests.post(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
            json={"input": {"video_url": public_url}},
            headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        ).json()
        job_id = runpod_resp.get("id")
        
        try:
            supabase.table("job_status").insert({"id": job_id, "email": "dev@mode.com", "status": "QUEUED"}).execute()
        except:
            pass
            
    st.success(f"✅ Mesin menyala! Job ID: `{job_id}`")
    st.info("Jangan tutup halaman ini. Video akan otomatis muncul di bawah saat proses selesai.")
    
    status_placeholder = st.empty()
    video_container = st.container()
    
    while True:
        headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        status_resp = requests.get(f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}", headers=headers).json()
        status = status_resp.get("status")
        
        if status == "COMPLETED":
            output = status_resp.get("output", {})
            
            # PROTEKSI BARU: Cek kalau AI diam-diam ngeluarin status Error
            if isinstance(output, dict) and output.get("status") == "error":
                status_placeholder.error(f"❌ MESIN NABRAK TEMBOK: {output.get('message')}")
                break
                
            status_placeholder.success("🔥 PANEN SELESAI! Klip siap dihajar ke TikTok.")
            clips = output.get("urls", [])
            
            with video_container:
                cols = st.columns(3)
                for i, clip in enumerate(clips):
                    with cols[i % 3]:
                        st.video(clip)
                        st.markdown(f"[⬇️ Download Klip]({clip})")
            break
        elif status in ["FAILED", "error"]:
            status_placeholder.error("❌ Mesin Gagal Panen. Tembok keamanan server RunPod jebol (Timeout).")
            break
        else:
            status_placeholder.warning(f"Status Mesin: {status} ... (AI sedang kerja keras membedah video, update tiap 5 detik)")
            time.sleep(5)