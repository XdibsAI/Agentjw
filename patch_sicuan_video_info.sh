#!/bin/bash
set -e
cd ~/agentjw
cp sicuan/brain.py "sicuan/brain.py.bak_videoinfo_$(date +%H%M%S)"

python3 - <<'PYEOF'
p = "sicuan/brain.py"
src = open(p, encoding="utf-8").read()

# ── 1. Add real video-render status to load_context() ───────────────────
old_ctx = '''        # Second brain: durable facts learned from past conversations'''

new_ctx = '''        # Video projects: REAL render status (never let the LLM guess this)
        try:
            from memory.memory_store import memory_store
            from pathlib import Path as _Path
            vids = [pr for pr in memory_store.list_projects() if pr["name"].startswith("video_")]
            if vids:
                ctx.append("\\nSTATUS RENDER VIDEO (DATA NYATA - jangan karang selain ini):")
                for v in vids:
                    final = _Path(v["project_dir"]) / "final_video.mp4"
                    if final.exists():
                        size_kb = final.stat().st_size // 1024
                        ctx.append(f"  - {v['name']}: ✅ SUDAH di-render ({size_kb} KB) -> {final}")
                    else:
                        ctx.append(f"  - {v['name']}: ⏳ belum di-render (hanya script/scenes, belum ada final_video.mp4)")
        except Exception:
            pass

        # Second brain: durable facts learned from past conversations'''

assert old_ctx in src, "anchor for video status not found"
src = src.replace(old_ctx, new_ctx, 1)

# ── 2. Add "video_info" to the action enum in the prompt ─────────────────
old_enum = '"action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project",'
new_enum = '"action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info",'
assert old_enum in src, "action enum not found"
src = src.replace(old_enum, new_enum, 1)

# Add a rule about video specs
old_rule = '''Kalau ada error terdeteksi: proactive mention di response
"""'''
new_rule = '''Kalau ada error terdeteksi: proactive mention di response

PENTING SOAL VIDEO: JANGAN PERNAH menyebutkan resolusi, fps, bitrate, codec,
atau spesifikasi teknis video apapun kecuali itu didapat dari action
"video_info" atau sudah tertulis di STATUS RENDER VIDEO di atas. Kalau user
tanya detail video, action = "video_info" dengan action_target = nama project.
Kalau project belum di-render, bilang jujur "belum di-render" — JANGAN karang spek.
"""'''
assert old_rule in src, "identity rule anchor not found"
src = src.replace(old_rule, new_rule, 1)

# ── 3. Implement video_info action with real ffprobe ─────────────────────
old_action_end = '''            elif action == "show_log":'''

new_action = '''            elif action == "video_info":
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
                        f"{p['name']} ({final}):\\n"
                        f"  Duration: {float(fmt.get('duration', 0)):.1f}s\\n"
                        f"  Size: {int(fmt.get('size', 0)) // 1024} KB\\n"
                        f"  Video: {vstream.get('width')}x{vstream.get('height')} "
                        f"{vstream.get('codec_name')} @ {vstream.get('r_frame_rate')}\\n"
                        f"  Audio: {astream.get('codec_name')} {astream.get('sample_rate')}Hz"
                    )
                except Exception as e:
                    size_kb = final.stat().st_size // 1024
                    return f"{p['name']}: file ada ({size_kb} KB) tapi ffprobe gagal: {e}"

            elif action == "show_log":'''

assert old_action_end in src, "show_log anchor not found"
src = src.replace(old_action_end, new_action, 1)

open(p, "w", encoding="utf-8").write(src)
print("✅ sicuan/brain.py patched (video_info + grounded video status)")
PYEOF

python3 -m py_compile sicuan/brain.py && echo "✅ syntax OK"
