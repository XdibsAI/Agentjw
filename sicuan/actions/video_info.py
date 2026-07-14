"""
video_info - Info video dengan Result Contract
"""

import subprocess
import json as _json
from pathlib import Path
# # Migrated to adapter  # Migrated to adapter
from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute video_info dengan Result Contract"""
    target = task.get("target", "")
    
    adapter = get_project_adapter()
    projects = adapter.get_projects()
    video_projects = [p for p in projects if p["name"].startswith("video_")]
    
    proj = None
    if target:
        for p in video_projects:
            if target.lower() in p["name"].lower():
                proj = p
                break
    elif video_projects:
        proj = video_projects[0]
    
    if not proj:
        contract = ResultContract(
            success=False,
            action="video_info",
            entity=target or "video",
            display=f"❌ Project video '{target}' tidak ditemukan" if target else "❌ Tidak ada project video ditemukan",
            errors=[f"Project video '{target}' tidak ditemukan" if target else "Tidak ada project video ditemukan"]
        )
        return contract.to_dict()
    
    final = Path(proj["project_dir"]) / "final_video.mp4"
    if not final.exists():
        contract = ResultContract(
            success=False,
            action="video_info",
            entity=proj['name'],
            display=f"❌ {proj['name']}: belum di-render (tidak ada final_video.mp4)",
            errors=[f"{proj['name']}: belum di-render"]
        )
        return contract.to_dict()
    
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
        
        duration = float(fmt.get('duration', 0))
        size = int(fmt.get('size', 0)) // 1024
        width = vstream.get('width')
        height = vstream.get('height')
        codec = vstream.get('codec_name')
        
        display = (
            f"{proj['name']} ({final}):\n"
            f"  Duration: {duration:.1f}s\n"
            f"  Size: {size} KB\n"
            f"  Video: {width}x{height} {codec}\n"
            f"  Audio: {astream.get('codec_name')} {astream.get('sample_rate')}Hz"
        )
        
        contract = ResultContract(
            success=True,
            action="video_info",
            entity=proj['name'],
            display=display,
            metrics={
                "duration": duration,
                "size_kb": size,
                "width": width,
                "height": height
            },
            confidence=0.95,
            data=info
        )
        return contract.to_dict()
        
    except subprocess.TimeoutExpired:
        contract = ResultContract(
            success=False,
            action="video_info",
            entity=proj['name'],
            display="❌ Timeout saat membaca info video",
            errors=["Timeout saat membaca info video"]
        )
        return contract.to_dict()
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="video_info",
            entity=proj['name'],
            display=f"❌ Gagal membaca info video: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
