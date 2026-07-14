"""
get_file - Ambil isi file dengan Result Contract
"""

from pathlib import Path
from mcp.tools.filesystem_tool import filesystem_tool
# # Migrated to adapter  # Migrated to adapter
from sicuan.core.result_contract import ResultContract
import re
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute get_file dengan Result Contract"""
    target = task.get("target", "")
    user_request = task.get("user_request", "")
    
    # Parse target: "project_name: file_path"
    proj_name = target
    file_path = None
    line_start = None
    line_end = None
    
    if target and ":" in target:
        proj_name, _, rest = target.partition(":")
        proj_name = proj_name.strip()
        rest = rest.strip()
        
        if "|" in rest:
            file_part, _, range_part = rest.partition("|")
            file_path = file_part.strip()
            range_part = range_part.strip()
            if "-" in range_part:
                try:
                    s, e = range_part.split("-")
                    line_start, line_end = int(s.strip()), int(e.strip())
                except ValueError:
                    pass
        else:
            file_path = rest
    
    # Fallback dari user_request
    if line_start is None and user_request:
        match = re.search(r'baris\s*(\d+)\s*[-sampai]+\s*(\d+)', user_request.lower())
        if match:
            line_start, line_end = int(match.group(1)), int(match.group(2))
    
    adapter = get_project_adapter()
    projects = adapter.get_projects()
    
    # Cari project
    proj = None
    for p in projects:
        if proj_name and proj_name.lower() in p["name"].lower():
            proj = p
            break
    
    if not proj:
        contract = ResultContract(
            success=False,
            action="get_file",
            entity=proj_name,
            display=f"❌ Project '{proj_name}' tidak ditemukan",
            errors=[f"Project '{proj_name}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    if not file_path:
        contract = ResultContract(
            success=False,
            action="get_file",
            entity=proj_name,
            display="❌ File path tidak ditentukan",
            errors=["File path tidak ditentukan"]
        )
        return contract.to_dict()
    
    project_dir = Path(proj["project_dir"])
    full_path = project_dir / file_path
    
    if not full_path.exists():
        contract = ResultContract(
            success=False,
            action="get_file",
            entity=f"{proj['name']}:{file_path}",
            display=f"❌ File '{file_path}' tidak ditemukan",
            errors=[f"File '{file_path}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    try:
        content = full_path.read_text()
        lines = content.splitlines()
        total_lines = len(lines)
        
        if line_start and line_end:
            start = max(0, line_start - 1)
            end = min(total_lines, line_end)
            selected = lines[start:end]
            display = f"📄 {proj['name']}/{file_path} — baris {line_start}-{line_end} dari {total_lines} total"
            data = {
                "file": file_path,
                "project": proj['name'],
                "total_lines": total_lines,
                "content": "\n".join(selected),
                "line_start": line_start,
                "line_end": line_end
            }
        else:
            display = f"📄 {proj['name']}/{file_path} — {total_lines} baris"
            data = {
                "file": file_path,
                "project": proj['name'],
                "total_lines": total_lines,
                "content": content
            }
        
        contract = ResultContract(
            success=True,
            action="get_file",
            entity=f"{proj['name']}:{file_path}",
            display=display,
            metrics={"total_lines": total_lines},
            confidence=1.0,
            data=data
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="get_file",
            entity=f"{proj['name']}:{file_path}",
            display=f"❌ Gagal membaca file: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
