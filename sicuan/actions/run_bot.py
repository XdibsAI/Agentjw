"""
run_bot - Jalankan bot trading dengan Result Contract
"""

import subprocess
import os
from pathlib import Path
from memory.unified_projects import unified_projects
from sicuan.core.result_contract import ResultContract


def execute(task: dict) -> dict:
    """Execute run_bot dengan Result Contract"""
    target = task.get("target", "")
    context = task.get("context", {})
    
    projects = unified_projects.list_projects()
    
    if not target:
        for p in projects:
            if "godmeme" in p["name"].lower() or "trading" in p["name"].lower():
                target = p["name"]
                break
        if not target and projects:
            target = projects[0]["name"]
    
    proj = None
    for p in projects:
        if target and target.lower() in p["name"].lower():
            proj = p
            break
    
    if not proj:
        contract = ResultContract(
            success=False,
            action="run_bot",
            entity=target,
            display=f"❌ Project '{target}' tidak ditemukan",
            errors=[f"Project '{target}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    project_dir = Path(proj["project_dir"])
    main_file = project_dir / "main.py"
    
    if not main_file.exists():
        contract = ResultContract(
            success=False,
            action="run_bot",
            entity=proj['name'],
            display=f"❌ main.py tidak ditemukan di {project_dir}",
            errors=[f"main.py tidak ditemukan di {project_dir}"]
        )
        return contract.to_dict()
    
    try:
        pid_file = project_dir / ".pid"
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                try:
                    os.kill(old_pid, 0)
                    contract = ResultContract(
                        success=True,
                        action="run_bot",
                        entity=proj['name'],
                        display=f"🤖 Bot {proj['name']} sudah running (PID: {old_pid})",
                        metrics={"pid": old_pid, "status": "already_running"},
                        confidence=0.95
                    )
                    return contract.to_dict()
                except OSError:
                    pid_file.unlink()
            except:
                pass
        
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        log_file = project_dir / "trading_bot_live.log"
        cmd = f"cd {project_dir} && nohup python3 main.py >> {log_file} 2>&1 &"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        import time
        time.sleep(0.5)
        
        result = subprocess.run(
            f"pgrep -f 'python3 main.py'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            pid = int(result.stdout.strip().split()[0])
            pid_file.write_text(str(pid))
            display = f"🤖 Bot {proj['name']} berhasil dijalankan (PID: {pid})"
            metrics = {"pid": pid, "status": "started"}
        else:
            display = f"🤖 Bot {proj['name']} berhasil di-start"
            metrics = {"status": "started"}
        
        contract = ResultContract(
            success=True,
            action="run_bot",
            entity=proj['name'],
            display=display,
            metrics=metrics,
            confidence=0.9
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="run_bot",
            entity=proj['name'],
            display=f"❌ Gagal menjalankan bot: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
