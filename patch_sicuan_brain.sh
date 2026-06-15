#!/bin/bash
set -e
cd ~/agentjw
cp sicuan/brain.py "sicuan/brain.py.bak_$(date +%H%M%S)"

python3 - <<'PYEOF'
p = "sicuan/brain.py"
src = open(p, encoding="utf-8").read()

# ── 1. Add fuzzy project matching helper ─────────────────────────────────
helper = '''
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
'''

anchor = "    def load_context(self) -> str:"
assert anchor in src, "load_context method not found"
src = src.replace(anchor, helper + "\n" + anchor, 1)

# ── 2. Use _find_project in scan_project and show_log ────────────────────
old_scan = '''            elif action == "scan_project":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = memory_store.list_projects()
                for p in projects:
                    if target.lower() in p["name"].lower():
                        data = filesystem_tool.scan_project(p["project_dir"])
                        return f"Scan {p['name']}: {data.get('valid_syntax',0)}/{data.get('total_py',0)} files valid"
                return f"Project '{target}' tidak ditemukan."'''

new_scan = '''            elif action == "scan_project":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = memory_store.list_projects()
                p = self._find_project(target, projects)
                if p:
                    data = filesystem_tool.scan_project(p["project_dir"])
                    return f"Scan {p['name']}: {data.get('valid_syntax',0)}/{data.get('total_py',0)} files valid"
                return f"Project '{target}' tidak ditemukan."'''

assert old_scan in src, "scan_project block not found"
src = src.replace(old_scan, new_scan, 1)

old_log = '''            elif action == "show_log":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = memory_store.list_projects()
                for p in projects:
                    if not target or target.lower() in p["name"].lower():
                        logs = filesystem_tool.read_log(p["project_dir"], lines=20)
                        return str(logs)[:500]
                return "Log tidak ditemukan."'''

new_log = '''            elif action == "show_log":
                from mcp.tools.filesystem_tool import filesystem_tool
                from memory.memory_store import memory_store
                projects = memory_store.list_projects()
                p = self._find_project(target, projects)
                if p:
                    logs = filesystem_tool.read_log(p["project_dir"], lines=20)
                    if isinstance(logs, dict) and logs.get("error"):
                        return f"Project '{p['name']}' ditemukan, tapi: {logs['error']} ({logs.get('searched','')})"
                    return f"[{p['name']}]\\n" + str(logs)[:500]
                return f"Log tidak ditemukan untuk '{target}'."'''

assert old_log in src, "show_log block not found"
src = src.replace(old_log, new_log, 1)

# ── 3. Inject second-brain memories into load_context() ───────────────────
old_ctx_end = '''        # Knowledge files
        for kname in ["identity", "jawarasa", "trading"]:'''

new_ctx_part = '''        # Second brain: durable facts learned from past conversations
        try:
            from memory.memory_store import memory_store
            mems = memory_store.recall(limit=8)
            if mems:
                ctx.append("\\nHAL YANG KAMU INGAT (second brain):")
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
                ctx.append("\\nSEMUA PROJECT LAIN:")
                for p in all_projects[5:15]:
                    ctx.append(f"  [{p['id'][:8]}] {p['name']} | {p['tool_type']} | {p['status']}")
        except Exception:
            pass

        # Knowledge files
        for kname in ["identity", "jawarasa", "trading"]:'''

assert old_ctx_end in src, "knowledge files block not found"
src = src.replace(old_ctx_end, new_ctx_part, 1)

open(p, "w", encoding="utf-8").write(src)
print("✅ sicuan/brain.py patched")
PYEOF

python3 -m py_compile sicuan/brain.py && echo "✅ syntax OK"
