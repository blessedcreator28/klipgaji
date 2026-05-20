import streamlit as st
import os
from supabase import create_client

# Konfigurasi
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Jagoan Clipper", layout="centered")
st.title("🔥 Jagoan Clipper Web")

# Blokir Link, Fokus Upload
st.write("Silakan upload video lo di bawah:")
uploaded_file = st.file_uploader("Pilih file video (MP4)", type=['mp4', 'mov'])

if uploaded_file is not None:
    if st.button("Generate Klip"):
        with st.spinner("Lagi upload ke sistem..."):
            # Upload ke Supabase Storage (Bucket 'videos')
            file_name = uploaded_file.name
            data = supabase.storage.from_("videos").upload(
                path=file_name,
                file=uploaded_file.getvalue(),
                file_options={"content-type": "video/mp4"}
            )
            
            # Ambil Public URL
            public_url = supabase.storage.from_("videos").get_public_url(file_name)
            st.success(f"Video berhasil diupload! Link: {public_url}")
            
            # Nanti di Step 2 kita sambungin ke RunPod pakai link ini
            st.info("Sekarang tinggal kita lempar ke RunPod. (Lanjut ke Step 2 nanti)")
else:
    st.warning("Link input tidak tersedia. Gunakan fitur upload di atas.")
