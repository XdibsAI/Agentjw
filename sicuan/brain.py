"""
SiCuan Brain - Bukan keyword/parsing/mapping
Semua keputusan dari LLM yang membaca konteks nyata
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import logger

BASE = Path(__file__).parent
KNOWLEDGE_DIR = BASE / "knowledge"
MEMORY_DIR = BASE / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

SICUAN_IDENTITY = """Kamu adalah SiCuan — Si Paling Cuan.
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
        # Handle "all", "semua" → return semua atau project pertama
        if t in ("all", "semua", "latest", "terbaru", "project", "projects"):
            return projects[0]

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

    def load_context(self) -> str:
        """Load semua konteks nyata dari disk"""
        ctx = []

        # Projects di memory
        try:
            from memory.memory_store import memory_store
            projects = memory_store.list_projects()
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
            vids = [pr for pr in memory_store.list_projects() if pr["name"].startswith("video_")]
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

        # Second brain: durable facts learned from past conversations
        try:
            from memory.memory_store import memory_store
            mems = memory_store.recall(limit=8)
            if mems:
                ctx.append("\nHAL YANG KAMU INGAT (second brain):")
                for m in mems:
                    ctx.append(f"  - {m['content'][:150]}")
        except Exception:
            pass

        # Show more projects (not just top 5) so older-but-relevant
        # projects (e.g. trading bots) aren't pushed out by recent video projects
        try:
            from memory.memory_store import memory_store
            all_projects = memory_store.list_projects()
            if len(all_projects) > 5:
                ctx.append("\nSEMUA PROJECT LAIN:")
                for p in all_projects[5:15]:
                    ctx.append(f"  [{p['id'][:8]}] {p['name']} | {p['tool_type']} | {p['status']}")
        except Exception:
            pass

        # Knowledge files — termasuk capabilities
        for kname in ["identity", "jawarasa", "trading", "capabilities"]:
            kf = KNOWLEDGE_DIR / f"{kname}.json"
            if kf.exists():
                try:
                    data = json.loads(kf.read_text())
                    ctx.append(f"\nKNOWLEDGE [{kname}]: {json.dumps(data, ensure_ascii=False)[:400]}")
                except Exception:
                    pass

        return "\n".join(ctx)

    def think_and_respond(self, user_message: str,
                          chat_history: List[Dict] = None) -> Dict:
        """
        Core brain — LLM membaca semua konteks dan decide:
        - Apa yang harus direspons
        - Action apa yang perlu diambil
        - Apa yang perlu diminta dari user
        """
        real_context = self.load_context()
        chat_history = chat_history or []

        # Build full system prompt dengan konteks nyata
        system = SICUAN_IDENTITY + f"""

DATA NYATA SEKARANG:
{real_context}

Berdasarkan data di atas, respond dengan JSON:
{{
  "response": "pesan ke user (bahasa natural, bukan template)",
  "action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info | get_file | move_to_gallery | list_media",
  "action_target": "nama project atau file yang perlu diaction",
  "needs_from_user": "null | api_key_name | konfirmasi | data_tambahan",
  "reasoning": "kenapa kamu decide ini (internal, tidak ditampilkan ke user)"
}}

Kalau ada API key kosong dan relevan dengan request user: action = request_api_key
Kalau user minta buat project: action = build_project
Kalau ada error terdeteksi: proactive mention di response

PENTING SOAL VIDEO: JANGAN PERNAH menyebutkan resolusi, fps, bitrate, codec,
atau spesifikasi teknis video apapun kecuali itu didapat dari action
"video_info" atau sudah tertulis di STATUS RENDER VIDEO di atas. Kalau user
tanya detail video, action = "video_info" dengan action_target = nama project.
Kalau project belum di-render, bilang jujur "belum di-render" — JANGAN karang spek.\nKalau user minta "buka/download file", action = "get_file"
Kalau user minta pindahkan/copy video ke gallery atau media, action = "move_to_gallery".
Kalau user minta lihat/list isi gallery atau media, action = "list_media". dengan action_target = nama project (dan nama file kalau disebut).
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
            logger.info(f"SiCuan decided: {result.get('action','chat')} | {result.get('reasoning','')[:60]}")
            return result
        except Exception as e:
            logger.error(f"SiCuan brain error: {e}")
            return {
                "response": "Waduh, ada yang ga beres di otak aku sebentar. Coba lagi ya Mas.",
                "action": None,
                "needs_from_user": None,
                "reasoning": str(e)
            }

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

    def execute_action(self, action: str, target: str,
                       user_request: str, session_id: str) -> str:
        """Execute action yang LLM decide"""
        try:
            if action == "cleanup_projects":
                from sicuan.cleanup import cleanup_report
                return cleanup_report()

            elif action == "delete_project":
                from sicuan.cleanup import delete_project, audit_projects
                # Cari project yang dimaksud
                projects = audit_projects()
                match = None
                for p in projects:
                    if (target and target.lower() in p["name"].lower()) or                        (target and target in p["id"]):
                        match = p
                        break
                if not match:
                    return "Project tidak ditemukan: " + str(target)
                result = delete_project(match["id"], delete_files=True)
                if result["success"]:
                    return f"✅ Deleted: {result['deleted']}\nBackup: {result['backup']}"
                return "Gagal: " + result["error"]

            elif action == "generate_image":
                from core.image_service import ImageService
                result = ImageService.generate(prompt=user_request)
                if result["success"]:
                    return f"Gambar berhasil dibuat: {result['path']} ({result.get('size_kb',0)}KB)"
                return f"Gagal generate gambar: {result['error']}"

            elif action == "build_project":
                # Check requirements dulu
                req_check = self.check_project_requirements(user_request)
                if req_check:
                    return req_check
                from agents.orchestrator import orchestrator
                result = orchestrator.execute(user_request, [], session_id)
                return f"Project '{target}' sedang dibangun. Status: {result.get('status','running')}"

            elif action == "repair_project":
                from agents.orchestrator import orchestrator
                result = orchestrator.execute("perbaiki " + target, [], session_id)
                return f"Repair selesai: {result.get('status','done')}"

            elif action == "run_bot":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                from tools.env_manager import env_manager
                from pathlib import Path as _Path
                projects = memory_store.list_projects(tool_type="trading")
                p = self._find_project(target, projects) or (projects[0] if projects else None)
                if not p:
                    return "Tidak ada trading bot yang ditemukan."

                project_dir = p["project_dir"]
                env_path = _Path(project_dir) / ".env"
                try:
                    required = env_manager.scan_required_vars(project_dir)
                    existing = env_manager.read_env_file(env_path) if env_path.exists() else {}
                    missing = [v for v in required if not existing.get(v) or existing.get(v) in ("your_key_here", "PASTE_YOUR_KEY_HERE")]
                except Exception:
                    missing = []

                if missing:
                    return (
                        f"{p['name']} belum bisa dijalankan — .env masih kosong untuk: {', '.join(missing)}.\n"
                        f"Kirim formatnya: " + ", ".join(f"{k}=nilainya" for k in missing)
                    )

                result = filesystem_tool.run_and_capture(project_dir, timeout=30)
                out = (result.get("stdout", "") or "")[:400]
                err = (result.get("stderr", "") or "")[:400]
                rc = result.get("returncode", result.get("exit_code", "?"))
                msg = f"{p['name']} dijalankan (exit code {rc}).\nSTDOUT:\n{out}"
                if err.strip():
                    msg += f"\nSTDERR:\n{err}"
                return msg

            elif action == "scan_project":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                from pathlib import Path as _Path
                projects = memory_store.list_projects()
                p = self._find_project(target, projects)
                if not p:
                    return f"Project '{target}' tidak ditemukan."
                data = filesystem_tool.scan_project(p["project_dir"])
                if data.get("total_py", 0) > 0:
                    return f"Scan {p['name']}: {data.get('valid_syntax',0)}/{data.get('total_py',0)} Python files valid"
                # Non-python (content/video) project — list its actual files instead
                d = _Path(p["project_dir"])
                files = sorted(f.name for f in d.iterdir() if f.is_file())
                return f"Scan {p['name']}: bukan project Python. Files: {', '.join(files)}"

            elif action == "get_file":
                from memory.memory_store import memory_store
                from pathlib import Path as _Path
                projects = memory_store.list_projects()
                p = self._find_project(target, projects)
                if not p:
                    return f"Project '{target}' tidak ditemukan."
                d = _Path(p["project_dir"])
                # If target also hints a filename (e.g. "video_x final_video.mp4"), try to match it
                candidates = sorted(f for f in d.iterdir() if f.is_file())
                pick = None
                for f in candidates:
                    if f.name.lower() in target.lower():
                        pick = f
                        break
                if not pick:
                    # default to final_video.mp4 if present, else first file
                    pick = next((f for f in candidates if f.name == "final_video.mp4"), candidates[0] if candidates else None)
                if not pick:
                    return f"{p['name']}: tidak ada file."
                rel = pick.relative_to(__import__("core.config", fromlist=["config"]).config.PROJECTS_DIR.parent)
                return f"File siap diunduh: {pick.name} ({pick.stat().st_size // 1024} KB)\nDownload: /files/download?path={rel}"

            elif action == "video_info":
                import subprocess, json as _json
                from pathlib import Path as _Path
                from memory.memory_store import memory_store
                projects = [pr for pr in memory_store.list_projects() if pr["name"].startswith("video_")]
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

            elif action == "show_log":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                trading_kw = ["trading","godmeme","bot","trade","sniper","solana"]
                is_trading = any(k in user_request.lower() for k in trading_kw)
                if is_trading or not target or target.lower() in ("all","semua",""):
                    logs = filesystem_tool.read_log("/home/dibs/agentjw/projects/godmeme_bot", lines=30)
                    if isinstance(logs, dict) and not logs.get("error"):
                        return str(logs)[:600]
                projects = memory_store.list_projects()
                p = self._find_project(target, projects)
                if p:
                    logs = filesystem_tool.read_log(p["project_dir"], lines=20)
                    if isinstance(logs, dict) and logs.get("error"):
                        return "Log tidak ditemukan di: " + p["name"]
                    return str(logs)[:500]
                # Fallback ke project pertama
                if projects:
                    logs = filesystem_tool.read_log(projects[0]["project_dir"], lines=20)
                    return str(logs)[:500]
                return "Tidak ada log yang ditemukan."

            elif action == "move_to_gallery":
                from memory.memory_store import memory_store
                import shutil
                projects = memory_store.list_projects()
                moved = []
                base = Path(__file__).parent.parent
                uploads = base / "uploads"
                uploads.mkdir(exist_ok=True)
                for proj in projects:
                    proj_dir = Path(proj.get("project_dir", ""))
                    for vid in proj_dir.glob("final_video.mp4"):
                        dest = uploads / f"{proj['name']}_final.mp4"
                        shutil.copy2(str(vid), str(dest))
                        moved.append(proj['name'])
                    for img in proj_dir.glob("preview.jpg"):
                        dest = uploads / f"{proj['name']}_preview.jpg"
                        shutil.copy2(str(img), str(dest))
                if moved:
                    return f"Dipindahkan ke gallery: {', '.join(moved)}"
                return "Tidak ada video/preview untuk dipindahkan."

            elif action == "list_media":
                base = Path(__file__).parent.parent
                items = list((base / "uploads").glob("*"))
                vids = [f.name for f in items if f.suffix == ".mp4"]
                imgs = [f.name for f in items if f.suffix in [".jpg",".png"]]
                return f"Gallery: {len(vids)} video, {len(imgs)} gambar.\n" + "\n".join([f.name for f in items[:20]])


        except Exception as e:
            return f"Error saat execute {action}: {e}"

sicuan_brain = SiCuanBrain()
