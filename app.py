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

st.set_page_config(page_title="Jagoan Clipper", layout="centered")
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stButton>button { border: 2px solid #FF7F50; color: #FF7F50; background-color: transparent; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #FF7F50; color: white; }
</style>
""", unsafe_allow_html=True)

# --- BYPASS LOGIN (SESSION ALWAYS AUTHENTICATED) ---
# Untuk sementara login dimatikan biar kerjaan lo gak terhambat
st.session_state.authenticated = True

# --- APP ---
st.title("🔥 Jagoan Clipper (Dev Mode)")
tab1, tab2 = st.tabs(["📁 Upload & Proses", "🔍 Cek Hasil Panen"])

with tab1:
    uploaded_file = st.file_uploader("Upload Video", type=['mp4', 'mov'])
    if uploaded_file and st.button("Proses Video"):
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            resp = requests.post("https://store1.gofile.io/uploadFile", files=files).json()
            public_url = resp['data']['downloadPage']
        
        with st.spinner("AI sedang membedah video..."):
            runpod_resp = requests.post(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
                json={"input": {"video_url": public_url}},
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            ).json()
            job_id = runpod_resp.get("id")
            # Simpan ke Supabase tanpa perlu login
            supabase.table("job_status").insert({"id": job_id, "email": "dev@mode.com", "status": "QUEUED"}).execute()
            st.success(f"✅ Berhasil! Job ID: `{job_id}`")

with tab2:
    job_id_input = st.text_input("Masukkan Job ID untuk cek hasil")
    if st.button("Cek Status"):
        with st.spinner("Menghubungi server AI..."):
            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            status_resp = requests.get(f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id_input}", headers=headers).json()
            status = status_resp.get("status")
            
            if status == "COMPLETED":
                st.success("🔥 Panen Selesai!")
                output = status_resp.get("output", {})
                clips = output.get("urls", [])
                for clip in clips:
                    st.video(clip)
                    st.markdown(f"[Download Klip]({clip})")
            else:
                st.warning(f"Status saat ini: {status}. Cek lagi dalam beberapa menit ya, Bro.")