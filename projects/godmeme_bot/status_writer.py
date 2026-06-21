"""
status_writer.py — Tulis status runtime godmeme_bot ke JSON
supaya SiCuan bisa baca kondisi real-time tanpa parsing log.
"""
import json
import os
import time
from pathlib import Path

STATUS_FILE = Path(__file__).parent / "godmeme_status.json"


def update_status(**kwargs):
    data = {}
    if STATUS_FILE.exists():
        try:
            data = json.loads(STATUS_FILE.read_text())
        except Exception:
            data = {}

    data["bot"] = "godmeme_bot"
    data["status"] = "running"
    data["pid"] = os.getpid()
    data["updated"] = time.time()
    data["updated_human"] = time.strftime("%Y-%m-%d %H:%M:%S")

    data.update(kwargs)

    STATUS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))