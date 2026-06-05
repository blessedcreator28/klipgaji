import runpod
import logging
import sys

# Konfigurasi logger biar langsung muncul
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

logger.info("--- [DEBUG] SCRIPT BERHASIL DIPANGGIL ---")

def handler(job):
    logger.info(f"--- [HANDLER] JOB DITERIMA: {job.get('id')} ---")
    return {"status": "success", "message": "Test successful"}

runpod.serverless.start({"handler": handler})