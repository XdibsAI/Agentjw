"""
SiCuan Nightly Consolidator — runs at 02:00
Analisa, bersihkan, dan upgrade diri sendiri
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).parent
DB = Path("/home/dibs/agentjw/memory/agentjw.db")


async def nightly_consolidation():
    """
    02:00 WIB: Cuan analisa hari ini, upgrade diri
    """
    import sys
    sys.path.insert(0, str(BASE.parent))
    from core.llm_client import llm
    from sicuan.memory_engine import memory_engine
    from mcp.tools.openclaw_tool import send_message

    print(f"[{datetime.now()}] Starting nightly consolidation...")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # 1. Ambil semua chat hari ini
    today = datetime.now().date().isoformat()
    chats = conn.execute("""
        SELECT role, content, timestamp FROM chat_history
        WHERE timestamp >= ?
        ORDER BY timestamp
    """, (today,)).fetchall()

    # 2. Ambil semua memories yang ada
    memories = conn.execute("""
        SELECT metadata, content, importance FROM memories
        ORDER BY importance DESC LIMIT 50
    """).fetchall()

    # 3. Work log hari ini
    worklogs = conn.execute("""
        SELECT project_name, action, detail FROM work_log
        WHERE timestamp >= ?
    """, (today,)).fetchall()

    conn.close()

    if not chats and not worklogs:
        print("Nothing to consolidate today")
        return

    # 4. LLM analisa dan decide
    chat_summary = "\n".join([
        f"{c['role']}: {c['content'][:100]}"
        for c in chats[-20:]
    ])

    work_summary = "\n".join([
        f"- {w['project_name']}: {w['action']} — {str(w['detail'])[:60]}"
        for w in worklogs
    ])

    existing_memory_topics = []
    for m in memories:
        try:
            meta = json.loads(m["metadata"] or "{}")
            existing_memory_topics.append(meta.get("topic", "unknown"))
        except Exception:
            existing_memory_topics.append("unknown")

    prompt = f"""Kamu SiCuan sedang melakukan nightly consolidation.
Ini yang terjadi hari ini:

CHAT HARI INI ({len(chats)} pesan):
{chat_summary}

PEKERJAAN HARI INI:
{work_summary}

MEMORY YANG SUDAH ADA:
{existing_memory_topics}

Tugasmu:
1. Extract insights baru yang belum ada di memory
2. Identify pola atau learning dari hari ini
3. Tentukan apakah ada cara ngobrol yang perlu diperbaiki
4. Buat ringkasan harian yang personal

Respond JSON:
{{
  "new_insights": [
    {{"topic": "...", "content": "...", "importance": 0.8}}
  ],
  "daily_summary": "ringkasan hari ini dalam 3-4 kalimat",
  "self_improvement": "apa yang perlu Cuan perbaiki dari cara kerjanya hari ini",
  "patterns_noticed": "pola atau tren yang Cuan notice",
  "cleanup_topics": ["topik memory lama yang sudah tidak relevan"]
}}"""

    try:
        raw = llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system="Kamu SiCuan dalam mode self-reflection. JSON only.",
            temperature=0.4,
            max_tokens=2000,
            json_mode=True,
        )
        data = json.loads(raw)

        # Simpan insights baru
        saved = 0
        for insight in data.get("new_insights", []):
            memory_engine.save_insight(
                topic=insight["topic"],
                content=insight["content"],
                importance=insight.get("importance", 0.7)
            )
            saved += 1

        # Simpan daily summary
        memory_engine.save_insight(
            topic=f"daily_summary_{today}",
            content=data.get("daily_summary", ""),
            importance=0.8
        )

        # Simpan self improvement notes
        if data.get("self_improvement"):
            memory_engine.save_insight(
                topic="self_improvement",
                content=f"[{today}] {data['self_improvement']}",
                importance=0.9
            )

        # Kirim summary ke Telegram
        summary_msg = (
            f"🌙 SiCuan Nightly Report ({today})\n\n"
            f"📊 {data.get('daily_summary', '')}\n\n"
            f"💡 Pattern: {data.get('patterns_noticed', '-')}\n\n"
            f"🔧 Self-improvement: {data.get('self_improvement', '-')}\n\n"
            f"💾 {saved} insights baru disimpan"
        )
        send_message(summary_msg)

        print(f"✓ Consolidation done: {saved} new insights")
        print(f"  Summary: {data.get('daily_summary','')[:100]}")

    except Exception as e:
        print(f"Consolidation error: {e}")


def run_consolidator():
    """Jalankan scheduler untuk nightly consolidation"""
    import schedule
    import time

    print("SiCuan Consolidator started")
    print("Scheduled: 02:00 WIB (19:00 UTC) daily")

    # 02:00 WIB = 19:00 UTC
    schedule.every().day.at("19:00").do(
        lambda: __import__('asyncio').run(nightly_consolidation())
    )

    # Test run manual kalau butuh
    # asyncio.run(nightly_consolidation())

    while True:
        schedule.run_pending()
        __import__('time').sleep(60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(nightly_consolidation())
