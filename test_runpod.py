import runpod

runpod.api_key = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
ENDPOINT_ID = "jt8nkdi8tyaz9x"

def run_test():
    print("🚀 SCRIPT DIMULAI...")
    try:
        print(f"📡 Menghubungi Endpoint: {ENDPOINT_ID}...")
        endpoint = runpod.Endpoint(ENDPOINT_ID)
        input_data = {"input": {"video_url": "https://www.youtube.com/shorts/8v_4QZ_T4_0", "command": "clip"}}
        job = endpoint.run(input_data)
        print(f"⌛ Job terkirim! ID: {job.job_id}")
        print("💡 Sedang menunggu mesin memproses video...")
        
        output = job.output(timeout=600)
        print("\n✅ BERHASIL! Ini jawaban dari server:")
        print("-" * 30)
        print(output)
        print("-" * 30)
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_test()
