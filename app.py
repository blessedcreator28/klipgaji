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

# --- BYPASS LOGIN ---
st.session_state.authenticated = True

# --- APP ---
st.title("🔥 Jagoan Clipper (Dev Mode)")
tab1, tab2 = st.tabs(["📁 Upload & Proses", "🔍 Cek Hasil Panen"])

with tab1:
    uploaded_file = st.file_uploader("Upload Video", type=['mp4', 'mov'])
    if uploaded_file and st.button("Proses Video"):
        with st.spinner("Mengamankan video ke brankas Supabase..."):
            # Bikin nama file unik biar gak bentrok
            file_ext = uploaded_file.name.split('.')[-1]
            unique_filename = f"input_raw_{int(time.time())}.{file_ext}"
            
            # Upload langsung ke Supabase (bucket 'videos')
            supabase.storage.from_("videos").upload(
                path=unique_filename,
                file=uploaded_file.getvalue(),
                file_options={"content-type": f"video/{file_ext}"}
            )
            
            # Ambil link video MENTAH (Jalur VIP)
            public_url = supabase.storage.from_("videos").get_public_url(unique_filename)
        
        with st.spinner("AI sedang membedah video..."):
            runpod_resp = requests.post(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
                json={"input": {"video_url": public_url}},
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            ).json()
            job_id = runpod_resp.get("id")
            
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
                output = status_resp.get("output", {})
                
                # Detektor Error (Biar gak dikibulin tulisan COMPLETED)
                if output.get("status") == "error":
                    st.error(f"❌ Mesin Gagal Panen: {output.get('message')}")
                    with st.expander("Bongkar Mesin (Log Error)"):
                        st.code(output.get("traceback", output.get("bukti_url", "No extra info")))
                else:
                    st.success("🔥 Panen Selesai!")
                    clips = output.get("urls", [])
                    if not clips:
                        st.warning("Proses selesai, tapi AI tidak menghasilkan klip satupun.")
                    for clip in clips:
                        st.video(clip)
                        st.markdown(f"[Download Klip]({clip})")
            else:
                st.warning(f"Status saat ini: {status}. Cek lagi dalam beberapa menit ya, Bro.")