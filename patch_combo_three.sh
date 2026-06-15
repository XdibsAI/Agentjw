#!/bin/bash
set -e
cd ~/agentjw
cp sicuan/brain.py "sicuan/brain.py.bak_combo_$(date +%H%M%S)"
cp api_server.py "api_server.py.bak_combo_$(date +%H%M%S)"

# ════════════════════════════════════════════════════════════════════════
# PART A — sicuan/brain.py: scan_project for non-py projects,
#          real run_bot with .env check, new "get_file" action
# ════════════════════════════════════════════════════════════════════════
python3 - <<'PYEOF'
p = "sicuan/brain.py"
src = open(p, encoding="utf-8").read()

# ── A1. scan_project: handle text-based (video/content) projects ─────────
old_scan = '''            elif action == "scan_project":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = memory_store.list_projects()
                p = self._find_project(target, projects)
                if p:
                    data = filesystem_tool.scan_project(p["project_dir"])
                    return f"Scan {p['name']}: {data.get('valid_syntax',0)}/{data.get('total_py',0)} files valid"
                return f"Project '{target}' tidak ditemukan."'''

new_scan = '''            elif action == "scan_project":
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
                return f"Scan {p['name']}: bukan project Python. Files: {', '.join(files)}"'''

assert old_scan in src, "scan_project block not found"
src = src.replace(old_scan, new_scan, 1)

# ── A2. run_bot: check .env required vars before running, real run+output ─
old_run = '''            elif action == "run_bot":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = memory_store.list_projects(tool_type="trading")
                if projects:
                    result = filesystem_tool.run_and_capture(projects[0]["project_dir"], timeout=10)
                    return f"Bot dijalankan. Output: {result.get('stdout','')[:200]}"
                return "Tidak ada trading bot yang ditemukan."'''

new_run = '''            elif action == "run_bot":
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
                        f"{p['name']} belum bisa dijalankan — .env masih kosong untuk: {', '.join(missing)}.\\n"
                        f"Kirim formatnya: " + ", ".join(f"{k}=nilainya" for k in missing)
                    )

                result = filesystem_tool.run_and_capture(project_dir, timeout=30)
                out = (result.get("stdout", "") or "")[:400]
                err = (result.get("stderr", "") or "")[:400]
                rc = result.get("returncode", result.get("exit_code", "?"))
                msg = f"{p['name']} dijalankan (exit code {rc}).\\nSTDOUT:\\n{out}"
                if err.strip():
                    msg += f"\\nSTDERR:\\n{err}"
                return msg'''

assert old_run in src, "run_bot block not found"
src = src.replace(old_run, new_run, 1)

# ── A3. New "get_file" action — returns a path the API can serve ─────────
old_video_info_anchor = '''            elif action == "video_info":'''
new_get_file = '''            elif action == "get_file":
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
                return f"File siap diunduh: {pick.name} ({pick.stat().st_size // 1024} KB)\\nDownload: /files/download?path={rel}"

            elif action == "video_info":'''

assert old_video_info_anchor in src, "video_info anchor not found"
src = src.replace(old_video_info_anchor, new_get_file, 1)

# Add to action enum + identity rule
old_enum = '"action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info",'
new_enum = '"action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info | get_file",'
assert old_enum in src
src = src.replace(old_enum, new_enum, 1)

old_rule_anchor = 'Kalau project belum di-render, bilang jujur "belum di-render" — JANGAN karang spek.'
new_rule_addition = old_rule_anchor + '\\nKalau user minta "buka/download file", action = "get_file" dengan action_target = nama project (dan nama file kalau disebut).'
assert old_rule_anchor in src
src = src.replace(old_rule_anchor, new_rule_addition, 1)

open(p, "w", encoding="utf-8").write(src)
print("✅ sicuan/brain.py patched (scan/run_bot/get_file)")
PYEOF

python3 -m py_compile sicuan/brain.py && echo "✅ brain.py syntax OK"

# ════════════════════════════════════════════════════════════════════════
# PART B — api_server.py: /files/download endpoint (serves any project file)
# ════════════════════════════════════════════════════════════════════════
python3 - <<'PYEOF'
p = "api_server.py"
src = open(p, encoding="utf-8").read()

anchor = '''@app.get("/projects")'''
assert anchor in src, "anchor /projects not found"

new_endpoint = '''@app.get("/files/download")
def download_file(path: str):
    """Serve a file by path relative to ~/agentjw (e.g. projects/video_xxx/final_video.mp4)."""
    try:
        base = Path(__file__).resolve().parent
        target = (base / path).resolve()
        if not str(target).startswith(str(base)):
            raise HTTPException(403, "Path outside project root")
        if not target.exists() or not target.is_file():
            raise HTTPException(404, "File not found")
        return FileResponse(str(target), filename=target.name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/projects")'''

src = src.replace(anchor, new_endpoint, 1)
open(p, "w", encoding="utf-8").write(src)
print("✅ api_server.py patched (/files/download)")
PYEOF

python3 -m py_compile api_server.py && echo "✅ api_server.py syntax OK"

echo "Restarting api_server..."
pkill -f 'uvicorn api_server' && sleep 1
nohup venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 18790 > api.log 2>&1 &
sleep 2
curl -s http://localhost:18790/health
