"""
from sicuan.core.autonomous_controller import AutonomousController

autonomous_controller = AutonomousController()
SiCuan Brain - Bukan keyword/parsing/mapping
Semua keputusan dari LLM yang membaca konteks nyata
"""
import json
import re
import os
from pathlib import Path
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import logger
from memory.unified_projects import unified_projects

BASE = Path(__file__).parent
KNOWLEDGE_DIR = BASE / "knowledge"
MEMORY_DIR = BASE / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

SICUAN_IDENTITY = """Kamu adalah SiCuan — Si Paling Cuan.

DATA KEJUJURAN (WAJIB):
1. Jika user meminta data historis (trade history, win rate, profit factor, dll):
   - Cek apakah data tersedia
   - Jika TIDAK tersedia, jawab: "Maaf, data trade history tidak tersedia. Saya perlu akses ke database trading."
   - JANGAN berjanji akan "mengambil data" jika data tidak ada
   - JANGAN mengarang angka atau statistik
2. Jika data tersedia, tunjukkan sumbernya (database, log, dll)
3. Lebih baik jujur "data tidak ada" daripada mengarang

AI partner bisnis yang benar-benar paham konteks, bukan bot template.

KARAKTER:
- Dengan yang lebih tua: hormat, panggil Mas/Pak/Bu, formal tapi hangat
- Dengan sesama: santai, bisa bercanda, pakai bahasa sehari-hari
- Kalau lawan bicara pakai Jawa: ikut pakai Jawa
- Tidak pernah template atau kaku
- Selalu berdasarkan DATA NYATA, bukan asumsi

KEMAMPUAN:
- Buat dan kelola project sampai benar-benar jalan
- Kalau ada API key kosong: LANGSUNG minta via chat, jangan diam
- Kalau ada error: explain dengan bahasa manusia, bukan stack trace
- Domain switching otomatis: desainer, analis trading, content creator, dll
- Proactive: kalau lihat peluang atau masalah, bilang duluan

ATURAN PENTING:
1. JANGAN pura-pura bisa kalau data tidak ada — bilang jujur
2. JANGAN tunggu disuruh kalau lihat ada yang perlu difix
3. SELALU gunakan data nyata dari filesystem, bukan karangan
4. Kalau minta API key, format: "Mas, [NAMA_KEY] belum ada di .env. Kirimkan ke sini ya, nanti langsung aku masukin dan test."
5. Ingat konteks percakapan — jangan tanya hal yang sudah dijawab
"""


class SiCuanBrain:
    def __init__(self):
        self._llm = None
        self._fs = None
        self.conversation_context = []

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    @property
    def fs(self):
        if self._fs is None:
            from mcp.tools.filesystem_tool import filesystem_tool
            self._fs = filesystem_tool
        return self._fs


    def _find_project(self, target: str, projects: List[Dict]) -> Optional[Dict]:
        """Fuzzy-match an LLM-provided target string to a project name.
        Handles cases where target is empty, a partial word, or a longer
        phrase that contains the project name (or vice-versa)."""
        if not projects:
            return None
        if not target:
            return projects[0]

        t = target.lower()
        # 1) exact / substring either direction
        for p in projects:
            name = p["name"].lower()
            if name in t or t in name:
                return p
        # 2) token overlap (split on non-alnum)
        import re as _re
        t_tokens = set(w for w in _re.split(r"[^a-z0-9]+", t) if len(w) > 2)
        for p in projects:
            name_tokens = set(w for w in _re.split(r"[^a-z0-9]+", p["name"].lower()) if len(w) > 2)
            if t_tokens & name_tokens:
                return p
        return None

    def load_context(self, user_message: str = "") -> str:
        """Load semua konteks nyata dari disk"""
        ctx = []

        # Projects di memory
        try:
            projects = unified_projects.list_projects()
            if projects:
                ctx.append("PROJECTS YANG ADA:")
                for p in projects[:5]:
                    ctx.append(f"  [{p['id'][:8]}] {p['name']} | {p['tool_type']} | {p['status']}")
                    ctx.append(f"  Dir: {p.get('project_dir','')}")
        except Exception:
            pass

        # Trading bot status
        try:
            bot_dir = "/home/dibs/agentjw/projects/godmeme_bot"
            logs = self.fs.read_log(bot_dir, lines=5)
            if logs and "error" not in str(logs).lower()[:50]:
                last_log = str(logs)[:300]
                ctx.append(f"\nTRADING BOT LOG TERAKHIR:\n{last_log}")
        except Exception:
            pass

        # .env check — cari yang kosong
        try:
            env_file = BASE.parent / ".env"
            if env_file.exists():
                missing = []
                for line in env_file.read_text().splitlines():
                    if "=" in line and not line.startswith("#"):
                        key, _, val = line.partition("=")
                        if not val.strip() or val.strip() in ("your_key_here", "PASTE_YOUR_KEY_HERE", ""):
                            missing.append(key.strip())
                if missing:
                    ctx.append(f"\nAPI KEYS KOSONG DI .env: {', '.join(missing)}")
        except Exception:
            pass

        # Daily memory
        try:
            daily = MEMORY_DIR / "daily_context.json"
            if daily.exists():
                data = json.loads(daily.read_text())
                ctx.append(f"\nKONTEKS HARI INI: {data.get('date','')[:10]}")
                ctx.append(f"Briefing tadi: {data.get('briefing','')[:200]}...")
        except Exception:
            pass

        # Video projects: REAL render status (never let the LLM guess this)
        try:
            from memory.memory_store import memory_store
            from pathlib import Path as _Path
            vids = [pr for pr in unified_projects.list_projects() if pr["name"].startswith("video_")]
            if vids:
                ctx.append("\nSTATUS RENDER VIDEO (DATA NYATA - jangan karang selain ini):")
                for v in vids:
                    final = _Path(v["project_dir"]) / "final_video.mp4"
                    if final.exists():
                        size_kb = final.stat().st_size // 1024
                        ctx.append(f"  - {v['name']}: ✅ SUDAH di-render ({size_kb} KB) -> {final}")
                    else:
                        ctx.append(f"  - {v['name']}: ⏳ belum di-render (hanya script/scenes, belum ada final_video.mp4)")
        except Exception:
            pass

        # Second brain: durable facts learned from past conversations.
        # TIDAK dibatasi ke 8 — model punya context window besar, jadi semua
        # insight penting (importance tinggi) di-include supaya benar-benar
        # ingat sejarah panjang, bukan cuma 8 fakta terakhir.
        try:
            from memory.memory_store import memory_store

            # Bagian 1: insight paling penting secara umum (importance tinggi)
            mems = memory_store.recall(limit=40)
            if mems:
                ctx.append("\nHAL YANG KAMU INGAT (second brain, urut prioritas):")
                for m in mems:
                    ctx.append(f"  - [{m['created_at'][:10]}] {m['content'][:200]}")

            # Bagian 2: insight yang RELEVAN dengan pertanyaan saat ini,
            # walau importance-nya tidak top — supaya pertanyaan spesifik
            # ("kemarin kita bahas apa soal X") tetap nyantol ke memory lama
            # yang relevan, bukan cuma yang dianggap "penting secara umum".
            if user_message:
                relevant = memory_store.search_memories(user_message, limit=10)
                if relevant:
                    ctx.append("\nHAL YANG RELEVAN DENGAN PERTANYAAN INI:")
                    for m in relevant:
                        ctx.append(f"  - [{m['created_at'][:10]}] {m['content'][:200]}")
        except Exception:
            pass

        # Show more projects (not just top 5) so older-but-relevant
        # projects (e.g. trading bots) aren't pushed out by recent video projects
        try:
            from memory.memory_store import memory_store
            all_projects = unified_projects.list_projects()
            if len(all_projects) > 5:
                ctx.append("\nSEMUA PROJECT LAIN:")
                for p in all_projects[5:15]:
                    ctx.append(f"  [{p['id'][:8]}] {p['name']} | {p['tool_type']} | {p['status']}")
        except Exception:
            pass

        # Knowledge files
        for kname in ["identity", "jawarasa", "trading"]:
            kf = KNOWLEDGE_DIR / f"{kname}.json"
            if kf.exists():
                try:
                    data = json.loads(kf.read_text())
                    ctx.append(f"\nKNOWLEDGE [{kname}]: {json.dumps(data, ensure_ascii=False)[:400]}")
                except Exception:
                    pass

        # Planner experience:
        # Ambil workflow lama supaya LLM belajar urutan penyelesaian masalah.
        try:
            from memory.memory_store import memory_store

            plans = memory_store.recall_plans(limit=5)

            if plans:
                ctx.append("\nPENGALAMAN PLANNER SEBELUMNYA:")

                for item in plans:
                    status = "SUCCESS" if item["success"] else "FAILED"

                    ctx.append(
                        f"  [{status}] {item['user_message'][:120]}"
                    )

                    if item.get("intent"):
                        ctx.append(
                            f"    Intent: {item.get('intent')} | "
                            f"Complexity: {item.get('complexity')} | "
                            f"Confidence: {item.get('confidence')}%"
                        )

                    steps = []
                    for step in item["plan"]:
                        steps.append(
                            step.get("action", "")
                        )

                    ctx.append(
                        f"    Workflow: {' -> '.join(steps)}"
                    )

        except Exception as e:
            logger.error(
                f"Planner context load failed: {e}"
            )

        return "\n".join(ctx)
        # === DATA AWARENESS ===
        # Cek apakah ada target project
        if hasattr(self, "_last_target"):
            target = self._last_target
            from pathlib import Path
            from memory.unified_projects import unified_projects
            project_dir = Path("/home/dibs/agentjw/projects") / target
            if not project_dir.exists():
                projects = unified_projects.list_projects()
                for p in projects:
                    if target.lower() in p["name"].lower():
                        project_dir = Path(p["project_dir"])
                        break
            db_path = project_dir / "trade_history.db" if project_dir.exists() else None
            if db_path and db_path.exists():
                ctx.append("\n[DATA] Trade history tersedia di " + str(db_path))
            else:
                ctx.append("\n[DATA] Trade history TIDAK tersedia. Data historis tidak dapat diakses.")

    def think_and_respond(self, user_message: str,
                          chat_history: List[Dict] = None) -> Dict:
        """
        Core brain — LLM membaca semua konteks dan decide:
        - Apa yang harus direspons
        - Action apa yang perlu diambil
        - Apa yang perlu diminta dari user
        """
        real_context = self.load_context(user_message)
        chat_history = chat_history or []

        # Build full system prompt dengan konteks nyata
        system = SICUAN_IDENTITY + f"""

DATA NYATA SEKARANG:
{real_context}

ATURAN PRIORITAS ROUTING (WAJIB):
Jika user memakai kata "cuan" tetapi TIDAK menyebut:
- godmeme
- trading
- PnL
- posisi
- SOL
- bot trading

dan konteksnya membahas "project kita", "project apa saja", "yang kita punya",
"aktif apa saja", maka pilih:
action = list_projects

Contoh:
User: "cuan untuk project kita apa"
Action: list_projects

JANGAN pilih godmeme_status untuk contoh tersebut.

godmeme_status hanya untuk pertanyaan spesifik trading Godmeme.


Berdasarkan data di atas, sebelum memilih action lakukan pemahaman request.

Tentukan:

1. intent:
- information
- diagnosis
- modification
- execution
- planning

2. complexity:
- simple (cukup satu action)
- compound (butuh beberapa data/action)

3. confidence:
- angka 0-100 seberapa yakin keputusanmu benar.

Jika compound:
buat plan berisi langkah yang dibutuhkan.

Format JSON WAJIB:

{{
  "intent": "jenis tujuan user",
  "complexity": "simple | compound",
  "confidence": 0,
  "plan": [
    {{
      "action": "nama action",
      "action_target": "target",
      "purpose": "kenapa langkah ini diperlukan"
    }}
  ],
  "response": "pesan ke user (bahasa natural, bukan template)",
  "action": "null | build_project | repair_project | modify_logic | modify_project | analyze_project | autonomous_project | run_bot | scan_project | get_file | show_log | trace_code | video_info | godmeme_status | list_projects | project_summary | business_analysis | gallery",
  "action_target": "untuk repair_project/modify_logic/analyze_project: format wajib nama_project: instruksi. Untuk action lain: nama project atau file saja.",
  "needs_from_user": "null | api_key_name | konfirmasi | data_tambahan",
  "reasoning": "kenapa kamu decide ini (internal, tidak ditampilkan ke user)"
}}

Kalau ada API key kosong dan relevan dengan request user: jelaskan di response, JANGAN pakai action terpisah (sudah dihandle natural language)
Kalau user minta buat project: action = build_project
Kalau user meminta daftar project, semua project, project kita, atau project aktif apa saja:
action = list_projects
Kalau user meminta audit, statistik, winrate, breakdown trade, tuning parameter, atau rekomendasi:
action = analyze_project

PRIORITAS INTENT CUAN:

Jika user bertanya hal STRATEGIS/BISNIS seperti:
- "mana yang paling cepat hasilkan uang"
- "kalau 7 hari fokus mana"
- "project mana harus dibuang"
- "buat roadmap cuan"
- "prioritas bisnis"
- "modal terbatas, fokus mana"
maka action = business_analysis (BUKAN project_summary)

Jika user hanya minta LIST/DAFTAR project (tanpa minta rekomendasi strategis):
action = list_projects atau project_summary

Jika user minta lihat video/gambar/gallery yang sudah dibuat:
action = gallery

Jika user bertanya:
- "cuan untuk project kita apa"
- "project yang menghasilkan uang"
- "mana project paling berpotensi"
- "peluang bisnis project"
- "saran semua project"
- "strategi monetisasi"

Gunakan action = project_summary.

Project_summary harus menjelaskan:
- project yang ada
- fungsi project
- potensi menghasilkan uang
- prioritas pengembangan

Jika user hanya meminta:
- daftar project
- semua project
- project kita apa saja

Gunakan action = list_projects.

JANGAN pilih godmeme_status untuk analisa project umum.

Gunakan godmeme_status HANYA jika user secara spesifik meminta:
- status godmeme
- trading godmeme
- posisi trading
- PnL bot
- balance SOL

Gunakan godmeme_status HANYA jika user secara spesifik meminta:
- status godmeme
- trading godmeme
- posisi trading
- PnL bot
- balance SOL
Kalau ada error terdeteksi: proactive mention di response


PEMISAHAN TARGET ENGINEERING (WAJIB):

SiCuan adalah ENGINEERING PARTNER yang memperbaiki project lain.

Jika user meminta perbaikan terhadap project tertentu:
- godmeme
- godmeme_bot
- bot trading
- database trading
- SELL/BUY logic
- posisi trading
- update DB
- error runtime project

Maka target WAJIB project tersebut.

Contoh:
User:
"perbaiki SELL godmeme, posisi tidak CLOSED di DB"

Benar:
action = modify_logic
action_target = "godmeme_bot: perbaiki update posisi CLOSED setelah SELL"

SALAH:
action_target = "sicuan: ..."


Target "sicuan" HANYA jika masalah berada di agent:
- planner salah memilih action
- router salah membaca intent
- coder agent gagal bekerja
- brain.py error
- memory SiCuan rusak
- executor SiCuan error

Jangan mengubah target ke sicuan hanya karena user memanggil "cuan".

PENTING SOAL REPAIR VS MODIFY VS ANALYZE:
Bedakan berdasarkan KONDISI FILE saat ini, bukan kata-kata di request user:

- "repair_project": pakai HANYA kalau kamu yakin file SAAT INI tidak bisa
  dijalankan sama sekali (syntax error, crash, exception traceback). Tanya
  diri sendiri: "kalau file ini dijalankan sekarang, apakah Python akan
  error sebelum sempat menjalankan logic apapun?" Kalau tidak yakin atau
  jawabannya "tidak", JANGAN pilih ini.

- "modify_logic": pakai kalau file BISA dijalankan tanpa crash, tapi
  PERILAKU/HASIL yang dihasilkan belum sesuai permintaan user — entah
  karena logic belum ada, logic salah, atau ada langkah yang terlewat.
  Kalau ragu antara repair_project dan modify_logic, PILIH modify_logic —
  karena modify_logic akan membaca isi file asli dulu sebelum mengubah
  apapun, jadi lebih aman untuk kasus yang tidak pasti.

- "analyze_project": pakai kalau user cuma ingin tahu/diagnosa kondisi
  sekarang, BELUM minta perubahan apapun.

- "get_file": WAJIB pakai kalau user minta LIHAT/TAMPILKAN isi kode asli,
  bukan minta diubah. JANGAN PERNAH menulis/mengarang isi kode di response
  kamu sendiri — kamu TIDAK PUNYA isi file sampai action get_file
  benar-benar dieksekusi dan hasilnya dikembalikan ke user secara otomatis.
  Kalau kamu menulis kode di field "response" padahal belum pernah baca file
  itu di STATUS/CONTEXT saat ini, itu karangan dan DILARANG.
  Format action_target: "nama_project: nama_file.py" (sebutkan file spesifik
  kalau user sebutkan, atau cuma "nama_project" untuk lihat daftar file dulu).

FORMAT action_target UNTUK repair_project, modify_logic, DAN analyze_project:
WAJIB diisi persis "nama_project: instruksi detail". Nama project harus
match dengan nama project yang ada (cek di STATUS PROJECTS di atas).
Jangan kosongkan, jangan isi cuma nama file tanpa nama project.
Contoh benar: "godmeme_bot: tambahkan update balance setelah SELL"

JANGAN PERNAH bilang "sudah diperbaiki" di response sebelum action benar-benar
dieksekusi dan diverifikasi. Tulis response netral seperti "aku cek dan
kerjakan dulu ya" — hasil verifikasi ditambahkan otomatis setelah action selesai.

Untuk action yang menghasilkan data:
(godmeme_status, list_projects, project_summary, scan_project, video_info)
response cukup pembuka singkat saja.
Jangan ulangi isi data karena executor akan menambahkan hasilnya.

PENTING SOAL VIDEO: JANGAN PERNAH menyebutkan resolusi, fps, bitrate, codec,
atau spesifikasi teknis video apapun kecuali itu didapat dari action
"video_info" atau sudah tertulis di STATUS RENDER VIDEO di atas. Kalau user
tanya detail video, action = "video_info" dengan action_target = nama project.
Kalau project belum di-render, bilang jujur "belum di-render" — JANGAN karang spek.
"""

        messages = []
        for h in chat_history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        try:
            raw = self.llm.chat(
                messages=messages,
                system=system,
                temperature=0.7,
                max_tokens=1000,
                json_mode=True,
            )
            result = json.loads(raw)

            # Simpan metadata planner terakhir untuk planner memory.
            self._last_intent = result.get("intent", "")
            self._last_complexity = result.get("complexity", "")
            self._last_confidence = int(result.get("confidence", 0) or 0)

            logger.info(
                f"SiCuan decided: {result.get('action','chat')} | "
                f"intent={self._last_intent} "
                f"confidence={self._last_confidence}"
            )
            return result
        except Exception as e:
            logger.error(f"SiCuan brain error: {e}")
            return {
                "response": "Waduh, ada yang ga beres di otak aku sebentar. Coba lagi ya Mas.",
                "action": None,
                "needs_from_user": None,
                "reasoning": str(e)
            }

    def reflect_and_maybe_continue(self, user_message: str, first_action: str,
                                    first_action_result: str, history: List[Dict]) -> Optional[str]:
        """
        Sinkronisasi reasoning: setelah 1 action faktual dieksekusi, cek apakah
        hasilnya SUDAH menjawab tuntas pertanyaan user, atau pertanyaan user
        sebenarnya butuh langkah lanjutan (misal "kenapa rugi" butuh status
        DULU baru analisa, bukan cuma status).

        Maksimal 1 putaran lanjutan — tidak infinite loop, tidak boros API call.
        Return None kalau hasil pertama sudah cukup (tidak ada perubahan).
        """
        eval_prompt = (
            f"User bertanya: \"{user_message}\"\n\n"
            f"Kamu sudah jalankan action '{first_action}' dan dapat hasil ini:\n"
            f"{first_action_result[:1500]}\n\n"
            f"Apakah hasil di atas SUDAH cukup menjawab pertanyaan user secara tuntas?\n"
            f"Kalau user tanya hal compound (misal \"kenapa rugi\" butuh data trade/analisa, "
            f"bukan cuma status saldo), dan hasil di atas BELUM mencakup itu — berarti BELUM cukup.\n\n"
            f"Jawab JSON:\n"
            f'{{"sufficient": true/false, "next_action": "nama action lanjutan atau null", '
            f'"next_action_target": "target untuk action lanjutan atau null", '
            f'"reasoning": "alasan singkat"}}\n\n'
            f"Action yang tersedia untuk lanjutan: analyze_project, show_log, list_projects, "
            f"scan_project, godmeme_status, project_summary, business_analysis.\n"
            f"Kalau next_action sama dengan action yang baru dijalankan ('{first_action}'), "
            f"set sufficient=true (jangan ulangi action yang sama)."
        )

        try:
            raw = self.llm.chat(
                messages=[{"role": "user", "content": eval_prompt}],
                system=(
                    "Kamu adalah reasoning evaluator untuk SiCuan. Tugasmu HANYA menilai "
                    "apakah hasil action sudah menjawab pertanyaan user secara tuntas, "
                    "bukan menjawab pertanyaan user sendiri."
                ),
                temperature=0.2,
                max_tokens=300,
                json_mode=True,
            )
            decision = json.loads(raw)
        except Exception as e:
            logger.error(f"Reflection eval failed: {e}")
            return None

        if decision.get("sufficient", True):
            return None

        next_action = decision.get("next_action")
        next_target = decision.get("next_action_target", "")
        if not next_action or next_action == first_action:
            return None

        logger.info(
            f"Reflection: action pertama belum cukup, lanjut ke '{next_action}' | "
            f"reason: {decision.get('reasoning','')[:80]}"
        )

        try:
            second_result = self.execute_action(next_action, next_target, user_message, "reflection")
        except Exception as e:
            logger.error(f"Reflection follow-up action failed: {e}")
            return None

        if not second_result:
            return None

        # Compose jawaban final: hasil pertama + hasil lanjutan, sintesis singkat
        synth_prompt = (
            f"User bertanya: \"{user_message}\"\n\n"
            f"DATA 1 ({first_action}):\n{first_action_result[:1000]}\n\n"
            f"DATA 2 ({next_action}):\n{second_result[:1500]}\n\n"
            f"Susun jawaban natural untuk user berdasarkan KEDUA data di atas. "
            f"Bahasa santai, actionable, jangan ulangi data mentah secara penuh — "
            f"sintesis insight-nya. Maksimal 400 kata."
        )
        try:
            final = self.llm.chat(
                messages=[{"role": "user", "content": synth_prompt}],
                system="Kamu SiCuan, AI partner bisnis. Sintesis data jadi insight actionable.",
                temperature=0.5,
                max_tokens=800,
            )
            return final
        except Exception as e:
            logger.error(f"Reflection synthesis failed: {e}")
            return first_action_result + "\n\n" + second_result

    def handle_api_key_submission(self, key_name: str, key_value: str) -> str:
        """User kirim API key — langsung tulis ke .env"""
        try:
            env_file = BASE.parent / ".env"
            content = env_file.read_text() if env_file.exists() else ""

            if key_name in content:
                # Update existing
                lines = content.splitlines()
                new_lines = []
                for line in lines:
                    if line.startswith(key_name + "="):
                        new_lines.append(f"{key_name}={key_value}")
                    else:
                        new_lines.append(line)
                env_file.write_text("\n".join(new_lines))
            else:
                # Add new
                env_file.write_text(content + f"\n{key_name}={key_value}\n")

            logger.info(f"API key set: {key_name}")
            return f"Oke, {key_name} sudah aku simpan ke .env. Lanjut test sekarang?"
        except Exception as e:
            return f"Gagal simpan {key_name}: {e}"

    def check_project_requirements(self, user_request: str) -> Optional[str]:
        """
        Cek apakah ada dependency atau env yang dibutuhkan project.
        Return pesan permintaan ke user kalau ada yang kurang.
        """
        req_lower = user_request.lower()
        missing = []

        # Cek env vars yang relevan
        env_file = BASE.parent / ".env"
        env_content = env_file.read_text() if env_file.exists() else ""

        def env_empty(key):
            import re
            m = re.search(rf"^{key}=(.*)$", env_content, re.MULTILINE)
            return not m or not m.group(1).strip() or m.group(1).strip() in (
                "your_key_here", "PASTE_YOUR_KEY_HERE", "")

        if "telegram" in req_lower or "bot" in req_lower:
            if env_empty("TELEGRAM_BOT_TOKEN"):
                missing.append(("TELEGRAM_BOT_TOKEN", "token bot Telegram kamu (dari @BotFather)"))

        if "youtube" in req_lower:
            if env_empty("YOUTUBE_API_KEY"):
                missing.append(("YOUTUBE_API_KEY", "YouTube Data API key dari Google Console"))

        if "openai" in req_lower or "gpt" in req_lower:
            if env_empty("OPENAI_API_KEY"):
                missing.append(("OPENAI_API_KEY", "OpenAI API key"))

        if missing:
            msgs = []
            for key, desc in missing:
                msgs.append(f"- **{key}**: {desc}")
            return (
                "Sebentar Mas, sebelum aku build — ada yang perlu aku minta dulu:\n\n" +
                "\n".join(msgs) +
                "\n\nKirimkan ke sini ya formatnya:\n" +
                "\n".join(f"`{k}=nilai_keynya`" for k,_ in missing) +
                "\n\nNanti langsung aku input ke .env dan test."
            )
        return None


    def execute_plan(self, plan, user_message: str, session_id: str = "planner") -> str:
        # Filter plan berdasarkan data availability
        target = None
        for step in plan:
            if step.get("target"):
                target = step.get("target")
                break
        if target:
            plan = filter_plan_by_data(plan, target)
        """
        Eksekusi multi-step plan dari planner.

        Plan menjadi source of truth:
        step 1 -> step 2 -> step 3

        Tidak memakai reflection loop sebagai pengganti planner.
        """

        if not plan:
            return ""

        results = []

        for index, step in enumerate(plan, start=1):
            try:
                action = step.get("action")
                target = step.get(
                    "action_target",
                    step.get("target", "")
                )

                if not action:
                    continue

                logger.info(
                    f"PLAN EXECUTOR step={index} action={action} target={target}"
                )

                result = self.execute_action(
                    action,
                    target,
                    user_message,
                    session_id
                )

                if result:
                    results.append(
                        {
                            "step": index,
                            "action": action,
                            "status": "success",
                            "result": result[:2000]
                        }
                    )
                else:
                    results.append(
                        {
                            "step": index,
                            "action": action,
                            "status": "empty",
                            "result": ""
                        }
                    )

            except Exception as e:
                logger.error(
                    f"PLAN EXECUTOR failed step={index}: {e}"
                )

                results.append(
                    {
                        "step": index,
                        "action": step.get("action"),
                        "status": "error",
                        "result": str(e)
                    }
                )

                break

        if not results:
            return ""

        # Simpan pengalaman planner ke persistent memory.
        # Tujuan:
        # - SiCuan ingat workflow yang pernah berhasil
        # - diagnosis compound berikutnya bisa belajar urutan action lama
        try:
            from memory.memory_store import memory_store

            planner_success = all(
                r.get("status") == "success"
                for r in results
            )

            memory_store.save_plan(
                user_message=user_message,
                plan=plan,
                result=json.dumps(
                    results,
                    ensure_ascii=False
                ),
                success=planner_success,
                intent=getattr(self, "_last_intent", ""),
                complexity=getattr(self, "_last_complexity", ""),
                confidence=getattr(self, "_last_confidence", 0)
            )

            logger.info(
                f"Planner memory saved: steps={len(plan)} success={planner_success}"
            )

        except Exception as e:
            logger.error(
                f"Planner memory save failed: {e}"
            )

        # Sintesis semua hasil plan
        synth_prompt = f"""
User:
{user_message}

HASIL EKSEKUSI PLAN:

{json.dumps(results, ensure_ascii=False, indent=2)}

Buat jawaban final:
- gunakan semua data
- jangan mengarang data baru
- bahasa natural
- actionable
"""

        try:
            final = self.llm.chat(
                messages=[
                    {
                        "role":"user",
                        "content": synth_prompt
                    }
                ],
                system=(
                    "Kamu SiCuan. "
                    "Sintesis hasil eksekusi menjadi jawaban final."
                ),
                temperature=0.4,
                max_tokens=800,
            )

            return final

        except Exception as e:
            logger.error(
                f"PLAN synthesis failed: {e}"
            )

            return "\n\n".join(
                r["result"]
                for r in results
                if r.get("result")
            )

    def execute_action(self, action: str, target: str,
                       user_request: str, session_id: str) -> str:
        from pathlib import Path
        """Execute action yang LLM decide"""
        try:
            if action == "build_project":
                # Check requirements dulu
                req_check = self.check_project_requirements(user_request)
                if req_check:
                    return req_check
                from agents.orchestrator import orchestrator
                result = orchestrator.execute(user_request, [], session_id)
                # Save artifact
                try:
                    from sicuan.core.artifact_event import ArtifactEvent, OutcomeEvent
                    from sicuan.core.artifact_subscribers import ArtifactSubscriberRegistry
                    event = ArtifactEvent(
                        session_id=session_id,
                        project=target,
                        action="build_project",
                        target=target
                    )
                    event.outcome = OutcomeEvent(
                        success=True,
                        result=str(result),
                        duration=0
                    )
                    registry = ArtifactSubscriberRegistry()
                    registry.publish(event)
                except Exception as e:
                    logger.error(f"Artifact save error: {e}")
                return f"Project '{target}' sedang dibangun. Status: {result.get('status','running')}"


            elif action == "modify_project":
                """
                Modify existing project berdasarkan request user.
                """

                from agents.orchestrator import orchestrator

                projects = unified_projects.list_projects()

                p = self._find_project(target, projects)

                if not p and "godmeme" in user_request.lower():
                    p = self._find_project("godmeme_bot", projects)

                if not p:
                    return f"Project '{target}' tidak ditemukan untuk dimodifikasi."

                from agents.auditor_agent import auditor_agent
                from pathlib import Path as _P

                instruction = f"""
Modifikasi project {p['name']}.

Request user:
{user_request}

Rules:
- Jangan merusak fitur existing
- Production ready
- Jelaskan perubahan
"""

                project_dir = _P(p["project_dir"])
                py_files = list(project_dir.glob("*.py"))
                before_snapshot = auditor_agent.snapshot([str(f) for f in py_files])

                result = orchestrator.execute(
                    instruction,
                    [],
                    session_id
                )

                verdict = auditor_agent.verify(
                    user_request=user_request,
                    before_snapshot=before_snapshot,
                    repair_result=result
                )

                return auditor_agent.format_response(verdict)


            elif action == "trace_code":
                from sicuan.code_trace import trace_before_patch
                symbol = (target or "").strip()
                if not symbol:
                    return "Mas, fungsi/symbol apa yang mau aku trace? Contoh: trace function _should_buy"
                result = trace_before_patch(symbol)
                return result.to_report()

            
            elif action == "analyze_project":

                from sicuan.project_trace import audit_project

                projects = unified_projects.list_projects()

                p = self._find_project(target, projects)

                if not p and "godmeme" in user_request.lower():
                    p = self._find_project(
                        "godmeme_bot",
                        projects
                    )

                if not p:
                    return "Project tidak ditemukan untuk analisa."

                audit = audit_project(
                    p["project_dir"]
                )

                lines = []

                lines.append(f"PROJECT: {p['name']}")
                lines.append(f"Trace confidence: {audit['confidence']}%")
                lines.append(f"Total functions: {audit['functions']}")
                lines.append("")
                lines.append("FEATURE CHECK:")

                for feat_name, meta in sorted(audit["features"].items()):
                    icon = "✅" if meta["exists"] else "⚠️"
                    lines.append(f"{icon} {feat_name}: {'FOUND' if meta['exists'] else 'MISSING'}")
                    for f in meta["files"][:3]:
                        lines.append(f"   - {f}")

                lines.append("")
                lines.append(
                    "Audit berbasis bukti file nyata (AST scan), bukan asumsi LLM."
                )

                return "\n".join(lines)



            elif action == "repair_project":
                from agents.orchestrator import orchestrator
                from agents.auditor_agent import auditor_agent

                # target bisa format "nama_project: instruksi" atau cuma nama
                proj_name = target
                if target and ":" in target:
                    proj_name, _, _ = target.partition(":")
                    proj_name = proj_name.strip()

                # Cari project dir untuk snapshot SEBELUM repair
                projects = unified_projects.list_projects()
                proj = None
                for p in projects:
                    if proj_name and proj_name.lower() in p["name"].lower():
                        proj = p
                        break

                if not proj:
                    return f"⚠️ Tidak bisa eksekusi: project '{proj_name}' tidak ditemukan di daftar project. Repair dibatalkan — tidak ada yang bisa diverifikasi tanpa project yang valid."

                project_dir = Path(proj["project_dir"])

                trace_ctx = must_trace_before_repair(
                    str(project_dir)
                )
                py_files = list(project_dir.glob("*.py"))
                before_snapshot = auditor_agent.snapshot([str(f) for f in py_files])

                result = orchestrator.execute("perbaiki " + target, [], session_id)

                verdict = auditor_agent.verify(
                    user_request=user_request,
                    before_snapshot=before_snapshot,
                    repair_result=result
                )

                # Auto-fallback dengan retry: repair tidak relevan -> coba
                # modify_logic, retry max 2x dengan reasoning auditor sebagai
                # feedback kalau attempt sebelumnya REJECTED.
                if verdict["verdict"] in ("NO_CHANGE", "REJECTED"):
                    from agents.specialist.logic_modifier import logic_modifier

                    attempt_instruction = user_request
                    fallback_verdict = None
                    max_retries = 2
                    attempt_i = 0
                    for attempt_i in range(max_retries):
                        fallback_snapshot = auditor_agent.snapshot([str(f) for f in py_files])
                        fallback_result = logic_modifier.modify_project(str(project_dir), attempt_instruction)
                        fallback_verdict = auditor_agent.verify(
                            user_request=user_request,
                            before_snapshot=fallback_snapshot,
                            repair_result=fallback_result
                        )
                        if fallback_verdict["verdict"] == "VERIFIED":
                            break
                        attempt_instruction = (
                            user_request +
                            "\n\nPERHATIAN: percobaan sebelumnya GAGAL diverifikasi. Alasan auditor: " +
                            fallback_verdict.get("reasoning", "") +
                            "\nPerbaiki dengan benar-benar menyentuh logic yang dimaksud user, "
                            "jangan cuma ubah cache/formatting/comment."
                        )

                    note = (
                        "_(repair_project tidak relevan, otomatis mencoba modify_logic "
                        "sebagai fallback — " + str(attempt_i + 1) + "x percobaan)_\n\n"
                    )
                    return note + auditor_agent.format_response(fallback_verdict)

                return auditor_agent.format_response(verdict)

            elif action == "modify_logic":
                from sicuan.core.repair_trace_guard import must_trace_before_repair, rank_functions_for_request
                from sicuan.core.feature_gap_engine import get_missing_repairs
                from agents.specialist.logic_modifier import logic_modifier
                from agents.auditor_agent import auditor_agent

                # target format: "nama_project: instruksi detail" ATAU cuma nama_project
                proj_name = target
                instruction = user_request
                if target and ":" in target:
                    proj_name, _, instruction_part = target.partition(":")
                    if instruction_part.strip():
                        instruction = instruction_part.strip()

                projects = unified_projects.list_projects()
                proj = None
                for p in projects:
                    if proj_name and proj_name.lower() in p["name"].lower():
                        proj = p
                        break

                if not proj:
                    return f"Project tidak ditemukan: {proj_name}"

                project_dir = Path(proj["project_dir"])

                
                trace_ctx = must_trace_before_repair(
                    str(project_dir)
                )

                if trace_ctx["confidence"] < 20:
                    return (
                        "TRACE FAILED\n"
                        f"project={project_dir}\n"
                        f"confidence={trace_ctx['confidence']}"
                    )

                py_files = list(project_dir.glob("*.py"))

                before_snapshot = auditor_agent.snapshot(
                    [str(f) for f in py_files]
                )

                repair_targets = rank_functions_for_request(
                    trace_ctx,
                    instruction
                )

                instruction = f"""
TRACE CONTEXT

confidence={trace_ctx["confidence"]}

features_found:
{trace_ctx["features_found"]}

features_missing:
{trace_ctx["features_missing"]}

function_count:
{trace_ctx["function_count"]}
repair_targets:
{repair_targets}

USER REQUEST:
{instruction}
"""

                feature_repairs = get_missing_repairs(trace_ctx)

                if feature_repairs:
                    instruction += "\n\nAUTO FEATURE GAP:\n"
                    for item in feature_repairs:
                        instruction += f"- {item['feature']}: {item['instruction']}\n"

                    target_files = []
                    for item in feature_repairs:
                        target_files.extend(item["targets"])
                    target_files = list(dict.fromkeys(target_files))[:2]

                    instruction += "\nFOCUS FILES:\n" + "\n".join(target_files) + "\n"

                result = logic_modifier.modify_project(
                    str(project_dir),
                    instruction
                )

                verdict = auditor_agent.verify(
                    user_request=instruction,
                    before_snapshot=before_snapshot,
                    repair_result=result
                )

                return auditor_agent.format_response(verdict)


            elif action == "autonomous_project":

                from pathlib import Path

                project_name = target.split(":")[0].strip()

                project_dir = (
                    Path("projects")
                    /
                    project_name
                )

                cycle = autonomous_controller.run_cycle(
                    project_dir
                )

                autonomous_controller.save_cycle_report(
                    project_dir,
                    cycle
                )

                return json.dumps(
                    cycle,
                    indent=2,
                    default=str
                )

            elif action == "run_bot":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = unified_projects.list_projects()
                if projects:
                    result = filesystem_tool.run_and_capture(projects[0]["project_dir"], timeout=10)
                    return f"Bot dijalankan. Output: {result.get('stdout','')[:200]}"
                return "Tidak ada trading bot yang ditemukan."

            elif action == "scan_project":
                from mcp.tools.filesystem_tool import filesystem_tool
                projects = unified_projects.list_projects()
                p = self._find_project(target, projects)
                if p:
                    data = filesystem_tool.scan_project(p["project_dir"])
                    return f"Scan {p['name']}: {data.get('valid_syntax',0)}/{data.get('total_py',0)} files valid"
                return f"Project '{target}' tidak ditemukan."

            elif action == "get_file":

                # target format: "nama_project: nama_file.py" atau
                # "nama_project: nama_file.py:start-end" atau cuma nama_project
                # Format: "nama_project: nama_file.py" atau
                # "nama_project: nama_file.py | start-end"
                proj_name = target
                filename = None
                line_start = None
                line_end = None
                if target and ":" in target:
                    proj_name, _, rest = target.partition(":")
                    proj_name = proj_name.strip()
                    rest = rest.strip()
                    if "|" in rest:
                        filename_part, _, range_part = rest.partition("|")
                        filename = filename_part.strip()
                        range_part = range_part.strip()
                        if "-" in range_part:
                            try:
                                s, e = range_part.split("-")
                                line_start, line_end = int(s.strip()), int(e.strip())
                            except ValueError:
                                pass
                    else:
                        filename = rest

                # Fallback: kalau LLM tidak masukkan range ke action_target,
                # cari pola "baris X-Y" / "baris X sampai Y" langsung dari
                # kalimat user. Ini jaring pengaman, bukan pengganti parsing utama.
                if line_start is None and user_request:
                    m = re.search(
                        r"baris\s+(\d+)\s*(?:-|sampai|s/d|hingga|ke)\s*(\d+)",
                        user_request, re.IGNORECASE
                    )
                    if m:
                        line_start, line_end = int(m.group(1)), int(m.group(2))

                # Fallback: kalau filename belum ketemu (LLM lupa sebutkan),
                # cari pola "nama_file.py" langsung dari kalimat user.
                if filename is None and user_request:
                    m2 = re.search(r"([a-zA-Z0-9_]+\.py)", user_request)
                    if m2:
                        filename = m2.group(1)

                projects = unified_projects.list_projects()
                p = self._find_project(proj_name, projects)
                if not p:
                    return f"Project '{proj_name}' tidak ditemukan."

                project_dir = Path(p["project_dir"])

                if filename:
                    fp = project_dir / filename
                    if not fp.exists():
                        py_files = sorted(f.name for f in project_dir.glob("*.py"))
                        return (
                            f"File '{filename}' tidak ditemukan di {p['name']}.\n"
                            f"File yang ada: {', '.join(py_files)}"
                        )
                    content_text = fp.read_text(errors="replace")
                    all_lines = content_text.splitlines()
                    line_count = len(all_lines)

                    if line_start is not None and line_end is not None:
                        # Range baris spesifik diminta
                        s = max(1, line_start)
                        e = min(line_count, line_end)
                        snippet = "\n".join(all_lines[s-1:e])
                        return (
                            f"📄 {p['name']}/{filename} — baris {s}-{e} dari {line_count} total "
                            f"(dibaca langsung dari disk):\n\n"
                            f"```python\n{snippet[:6000]}\n```"
                        )

                    # Tidak ada range -> tampilkan awal + kasih tahu cara lihat lanjutan
                    return (
                        f"📄 {p['name']}/{filename} ({line_count} baris, dibaca langsung dari disk):\n\n"
                        f"```python\n{content_text[:6000]}\n```"
                        + (
                            f"\n\n_(dipotong — file punya {line_count} baris. "
                            f"Minta baris tertentu, misal \"tampilkan {filename} baris "
                            f"200-400 di {p['name']}\" untuk lihat bagian lain.)_"
                            if len(content_text) > 6000 else ""
                        )
                    )
                else:
                    py_files = sorted(f.name for f in project_dir.glob("*.py"))
                    return (
                        f"📂 {p['name']} ({project_dir}):\n"
                        + "\n".join(f"  - {f}" for f in py_files)
                        + "\n\nSebutkan nama file spesifik untuk lihat isinya."
                    )

            elif action == "video_info":
                import subprocess, json as _json
                from pathlib import Path as _Path
                from memory.memory_store import memory_store
                projects = [pr for pr in unified_projects.list_projects() if pr["name"].startswith("video_")]
                p = self._find_project(target, projects)
                if not p:
                    return f"Project video '{target}' tidak ditemukan."
                final = _Path(p["project_dir"]) / "final_video.mp4"
                if not final.exists():
                    return f"{p['name']}: belum di-render (tidak ada final_video.mp4). Ketik 'render videonya' untuk project ini dulu."
                try:
                    r = subprocess.run(
                        ["ffprobe", "-v", "quiet", "-print_format", "json",
                         "-show_format", "-show_streams", str(final)],
                        capture_output=True, text=True, timeout=15
                    )
                    info = _json.loads(r.stdout)
                    fmt = info.get("format", {})
                    vstream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
                    astream = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {})
                    return (
                        f"{p['name']} ({final}):\n"
                        f"  Duration: {float(fmt.get('duration', 0)):.1f}s\n"
                        f"  Size: {int(fmt.get('size', 0)) // 1024} KB\n"
                        f"  Video: {vstream.get('width')}x{vstream.get('height')} "
                        f"{vstream.get('codec_name')} @ {vstream.get('r_frame_rate')}\n"
                        f"  Audio: {astream.get('codec_name')} {astream.get('sample_rate')}Hz"
                    )
                except Exception as e:
                    size_kb = final.stat().st_size // 1024
                    return f"{p['name']}: file ada ({size_kb} KB) tapi ffprobe gagal: {e}"

            elif action == "list_projects":
                from memory.project_registry import ProjectRegistry

                registry = ProjectRegistry()
                projects = registry.list_projects()

                if not projects:
                    return "Belum ada project terdaftar."

                text = "📂 DAFTAR PROJECT KITA:\n\n"

                for p in projects:
                    text += (
                        f"• {p[0]}\n"
                        f"  Status: {p[4]}\n"
                        f"  Path: {p[1]}\n\n"
                    )

                return text

            elif action == "gallery":
                from memory.media_registry import gallery_summary, scan_and_index
                scan_and_index()  # refresh dulu
                return gallery_summary()

            elif action == "business_analysis":

                projects = unified_projects.list_projects()
                if not projects:
                    return "Belum ada project untuk dianalisa."

                context_lines = []
                for p in projects:
                    context_lines.append(
                        f"- {p['name']} (tipe: {p['tool_type']}, status: {p['status']}, "
                        f"{p['python_files']} file Python, path: {p['project_dir']})"
                    )

                prompt = (
                    "Sebagai SiCuan, analisa bisnis dari SEMUA project berikut (total " + str(len(projects)) + " project):\n\n" +
                    "\n".join(context_lines) +
                    "\n\nUser bertanya: " + user_request +
                    "\n\nWAJIB bahas SEMUA project di atas satu per satu, jangan cuma satu. "
                    "Beri rekomendasi konkret: mana yang paling potensial cuan, mana yang harus didrop, "
                    "dan urutan prioritas kalau punya waktu/modal terbatas. Jawab natural, actionable, bahasa santai."
                )

                from core.llm_client import llm
                analysis = llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system="Kamu SiCuan, AI partner bisnis yang to-the-point dan strategis. SELALU bahas semua project yang diberikan, jangan skip satupun.",
                    temperature=0.6, max_tokens=1000
                )
                return analysis

            elif action == "list_projects" or action == "project_summary":

                from memory.project_registry import ProjectRegistry

                registry = ProjectRegistry()
                projects = registry.list_projects()

                if not projects:
                    return "Belum ada project terdaftar."

                if action == "list_projects":

                    text = "📂 DAFTAR PROJECT KITA:\n\n"

                    for p in projects:
                        name = p[0]
                        path = p[1]
                        status = p[4]

                        text += (
                            f"• {name}\n"
                            f"  Status: {status}\n"
                            f"  Path: {path}\n\n"
                        )

                    return text


                if action == "project_summary":

                    text = "💰 ANALISA PROJECT KITA:\n\n"

                    for p in projects:
                        name = p[0]
                        path = p[1]
                        status = p[4]

                        text += (
                            f"📌 {name}\n"
                            f"Status: {status}\n"
                            f"Path: {path}\n"
                        )

                        if name == "godmeme_bot":
                            text += (
                                "Fungsi: Trading bot Solana DEX\n"
                                "Potensi cuan:\n"
                                "- Automation trading\n"
                                "- Signal subscription\n"
                                "- Telegram trading alert\n"
                                "Prioritas:\n"
                                "- Optimasi strategi\n"
                                "- Risk management\n"
                                "- Validasi profit paper trading\n"
                            )

                        elif name == "flask_todo_api":
                            text += (
                                "Fungsi: Backend API service\n"
                                "Potensi cuan:\n"
                                "- SaaS micro product\n"
                                "- API berbayar\n"
                                "- Template deployment\n"
                                "Prioritas:\n"
                                "- Tambah fitur premium\n"
                                "- Deploy production\n"
                                "- Monetisasi user\n"
                            )

                        else:
                            text += (
                                "Potensi cuan: perlu analisa lanjutan\n"
                            )

                        text += "\n"

                    return text

            elif action == "godmeme_status":
                from projects.godmeme_bot.status_sync_provider import get_godmeme_status

                data = get_godmeme_status()

                process = data.get("process", {})
                database = data.get("database", {})
                positions = data.get("positions", [])

                pos_text = ""
                if positions:
                    pos_text = "\n\nOpen Positions:\n"
                    for p in positions[:5]:
                        pos_text += (
                            f"- {p.get('symbol','-')} "
                            f"{p.get('amount','-')} SOL "
                            f"entry {p.get('entry','-')}\n"
                        )

                return (
                    "🤖 GODMEME STATUS\n"
                    f"Process: {'RUNNING' if process.get('alive') else 'STOPPED'}\n"
                    f"PID: {process.get('pid','-')}\n"
                    f"Mode: {data.get('mode','-')}\n"
                    f"Balance: {data.get('balance','-')} SOL\n\n"
                    f"Trades: {database.get('trades',0)}\n"
                    f"BUY: {database.get('buy',0)}\n"
                    f"SELL: {database.get('sell',0)}\n"
                    f"Realized PnL: {database.get('realized_pnl',0):+.6f} SOL\n\n"
                    f"Last Event: {data.get('last_event','-')}"
                    + pos_text
                )

            elif action == "show_log":

                target_lower = str(target).lower()

                if "godmeme" in target_lower:

                    project_dir = "/home/dibs/agentjw/projects/godmeme_bot"

                    candidates = [
                        "trading_bot_live.log",
                        "paper_24h.log",
                        "trading_bot_live_old.log",
                        "trading_bot.log"
                    ]

                    for f in candidates:

                        path = os.path.join(project_dir, f)

                        if os.path.exists(path):

                            with open(path, "r", errors="ignore") as fp:
                                lines = fp.readlines()

                            return (
                                f"LOG FILE: {f}\n\n"
                                + "".join(lines[-200:])
                            )

                    return "Tidak ada log ditemukan pada godmeme_bot."

                log_file = Path(target)

                if log_file.exists():

                    lines = log_file.read_text(
                        errors="ignore"
                    ).splitlines()

                    return "\n".join(lines[-200:])

                return f"Log tidak ditemukan: {target}"

        except Exception as e:
                    return (
                        f"Gagal membaca log: {e}"
                    )

        except Exception as e:
            return f"Error saat execute {action}: {e}"

        return "Action tidak dikenali."




sicuan_brain = SiCuanBrain()
