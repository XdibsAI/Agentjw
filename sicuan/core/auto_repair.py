"""
Auto-Repair Functions — Terpisah dari brain.py
"""

from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import subprocess
import sys
import importlib.util


def preflight_check(file_path: str) -> Dict:
    """Run preflight validation"""
    from sicuan.core.preflight import get_preflight
    preflight = get_preflight()
    return preflight.check(file_path)


def resolve_target(user_request: str, candidates: List[Dict]) -> Optional[Dict]:
    """Resolve target dengan TargetResolver"""
    from sicuan.core.target_resolver import get_target_resolver
    resolver = get_target_resolver()
    return resolver.resolve(user_request, candidates)


def apply_patch(file_path: str, operation: Dict) -> Dict:
    """Apply patch ke file"""
    from sicuan.core.patch_engine import get_patch_engine, PatchOperation

    engine = get_patch_engine()

    op = PatchOperation(
        type=operation.get("type", "add_method"),
        file=file_path,
        target=operation.get("target", ""),
        content=operation.get("content", ""),
        class_name=operation.get("class_name", "Strategy")
    )

    return engine.apply(op)


def verify_runtime(file_path: str) -> Dict:
    """
    Verify runtime setelah patch
    - Compile dulu
    - Import dengan importlib.util (bukan __import__ string)
    """
    # 1. Compile
    result = subprocess.run(
        ["python3", "-m", "py_compile", file_path],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode != 0:
        return {"success": False, "error": result.stderr[:200], "stage": "compile"}

    # 2. Import menggunakan importlib.util (lebih reliable)
    try:
        file_path_obj = Path(file_path)
        module_name = file_path_obj.stem  # Ambil nama file tanpa .py
        
        # Cari di sys.path atau build spec
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return {"success": False, "error": f"Cannot create spec for {file_path}", "stage": "import"}
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Simpan di sys.modules untuk import berikutnya
        sys.modules[module_name] = module
        
        return {"success": True, "message": f"Runtime OK: {module_name} imported"}
        
    except Exception as e:
        return {"success": False, "error": str(e)[:200], "stage": "import"}


def auto_fix_error(error_message: str, max_attempts: int = 3) -> Dict:
    """Auto fix error — full pipeline"""
    from sicuan.brain import SiCuanBrain
    brain = SiCuanBrain()

    # 1. Diagnose
    diagnosis = brain.diagnose_error(error_message)
    action = diagnosis.get("action")

    if action == "modify_logic":
        # Execute modify_logic
        result = brain.execute_action(
            action="modify_logic",
            target="godmeme_bot: " + diagnosis.get("fix", ""),
            user_request=diagnosis.get("fix", ""),
            session_id="auto_fix"
        )

        # Verify
        verification = verify_runtime("projects/godmeme_bot/strategy.py")
        if verification["success"]:
            return {"success": True, "result": result, "verification": verification}
        else:
            return {"success": False, "result": result, "verification": verification}

    return {"success": False, "message": f"Unknown action: {action}"}

# Patch Engine
try:
    from sicuan.core.patch_engine import get_patch_engine, PatchOperation
except ImportError:
    print("[WARN] Patch Engine not available")
    def get_patch_engine():
        return None
