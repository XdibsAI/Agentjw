#!/bin/bash
set -e
cd ~/agentjw
cp agents/orchestrator.py "agents/orchestrator.py.bak_step2_$(date +%H%M%S)"

python3 - <<'PYEOF'
p = "agents/orchestrator.py"
src = open(p, encoding="utf-8").read()

# 1) Remove the old duplicate snippet injection (now handled inside the
#    system prompt template via THINGS YOU REMEMBER ... block from step 1)
old_dup = '''
        if snippets:
            system += "\\nMEMORY:\\n" + "\\n".join(f"- {s[:120]}" for s in snippets)
'''
if old_dup in src:
    src = src.replace(old_dup, "\n")
    print("removed duplicate MEMORY injection")
else:
    print("duplicate MEMORY injection not found (already removed?)")

# 2) Add auto memory extraction right before `return response`
old_tail = '''        memory_store.save_chat(session_id, "user", user_message)
        memory_store.save_chat(session_id, "assistant", response)
        return response'''

new_tail = '''        memory_store.save_chat(session_id, "user", user_message)
        memory_store.save_chat(session_id, "assistant", response)

        # ── Second brain: extract & store durable facts from this turn ─────
        try:
            memory_agent.run({
                "action": "extract_and_store",
                "session_summary": f"User: {user_message}\\nAssistant: {response[:1000]}",
                "success": True,
                "project_name": session_id,
            })
        except Exception as e:
            console.print(f"[dim]Memory extraction skipped: {e}[/dim]")

        return response'''

assert old_tail in src, "chat() return block not found"
src = src.replace(old_tail, new_tail, 1)

open(p, "w", encoding="utf-8").write(src)
print("✅ orchestrator.py patched (auto memory extraction)")
PYEOF

python3 -m py_compile agents/orchestrator.py && echo "✅ syntax OK"

echo "Restarting api_server..."
pkill -f 'uvicorn api_server' && sleep 1
nohup venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 18790 > api.log 2>&1 &
sleep 2
curl -s http://localhost:18790/health
