#!/bin/bash
set -e
cd ~/agentjw
cp memory/memory_store.py "memory/memory_store.py.bak_$(date +%H%M%S)"
cp agents/orchestrator.py "agents/orchestrator.py.bak_$(date +%H%M%S)"

# ── 1. memory_store.py: keyword-based search instead of full-sentence LIKE ──
python3 - <<'PYEOF'
p = "memory/memory_store.py"
src = open(p, encoding="utf-8").read()

old = '''    def search_memories(self, query: str, type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            if type:
                rows = conn.execute("SELECT id,type,content,metadata,importance,created_at FROM memories WHERE type=? AND content LIKE ? ORDER BY importance DESC LIMIT ?",
                    (type, f"%{query}%", limit)).fetchall()
            else:
                rows = conn.execute("SELECT id,type,content,metadata,importance,created_at FROM memories WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
                    (f"%{query}%", limit)).fetchall()
        return [{"id": r[0], "type": r[1], "content": r[2], "metadata": json.loads(r[3]), "importance": r[4], "created_at": r[5]} for r in rows]'''

new = '''    def search_memories(self, query: str, type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        # Keyword-based OR matching: split query into significant words
        # (len > 3) and match any of them, instead of requiring the whole
        # sentence to appear verbatim (which almost never happens).
        words = [w for w in query.lower().split() if len(w) > 3][:6]
        if not words:
            return self.recall(type=type, limit=limit)

        conditions = " OR ".join(["lower(content) LIKE ?"] * len(words))
        params: List = [f"%{w}%" for w in words]

        sql = f"SELECT id,type,content,metadata,importance,created_at FROM memories WHERE ({conditions})"
        if type:
            sql += " AND type=?"
            params.append(type)
        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()

        seen = set()
        results = []
        for r in rows:
            if r[0] in seen:
                continue
            seen.add(r[0])
            results.append({"id": r[0], "type": r[1], "content": r[2], "metadata": json.loads(r[3]), "importance": r[4], "created_at": r[5]})
        return results'''

assert old in src, "search_memories block not found — check memory_store.py manually"
src = src.replace(old, new)
open(p, "w", encoding="utf-8").write(src)
print("✅ memory_store.py patched (keyword search)")
PYEOF

# ── 2. orchestrator.py: inject retrieved snippets into prompt + auto-extract after response ──
python3 - <<'PYEOF'
p = "agents/orchestrator.py"
src = open(p, encoding="utf-8").read()

# 2a) Make sure retrieved snippets get injected into the system prompt
old_proj_ctx = '''PROJECTS ({len(projects)} total):
{proj_ctx}
{real_data}'''

new_proj_ctx = '''PROJECTS ({len(projects)} total):
{proj_ctx}
{real_data}

THINGS YOU REMEMBER ABOUT THIS USER/PROJECT (from past conversations):
{chr(10).join(f"- {s}" for s in snippets) if snippets else "(belum ada memori relevan)"}'''

assert old_proj_ctx in src, "PROJECTS block not found in chat() system prompt"
src = src.replace(old_proj_ctx, new_proj_ctx, 1)

open(p, "w", encoding="utf-8").write(src)
print("✅ orchestrator.py patched (inject memory snippets into prompt)")
PYEOF

python3 -m py_compile memory/memory_store.py agents/orchestrator.py
echo "✅ syntax OK"
