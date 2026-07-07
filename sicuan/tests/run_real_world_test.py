#!/usr/bin/env python3
"""Test SiCuan pada real-world repository (FastAPI) - FIXED VERSION"""

import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.core.repair_pipeline import RepairPipeline
from sicuan.core.preflight import get_preflight


def test_real_world():
    """Test pada FastAPI repository"""
    repo_dir = Path("/tmp/fastapi/fastapi")
    if not repo_dir.exists():
        print("❌ FastAPI not found. Run: git clone https://github.com/fastapi/fastapi.git /tmp/fastapi")
        return
    
    print("="*60)
    print("REAL-WORLD TEST: FastAPI Repository")
    print("="*60)
    
    # Cari file Python
    py_files = list(repo_dir.rglob("*.py"))
    # Filter out __pycache__, test files
    py_files = [f for f in py_files if "__pycache__" not in str(f) and "test" not in str(f).lower()]
    print(f"Found {len(py_files)} Python files")
    
    # Test up to 10 files (random)
    test_files = random.sample(py_files, min(10, len(py_files)))
    
    results = []
    total_time = 0
    healthy_count = 0
    repaired_count = 0
    failed_count = 0
    
    for i, file_path in enumerate(test_files):
        print(f"\n[{i+1}/{len(test_files)}] Testing: {file_path.name}")
        start = time.time()
        
        # Cek apakah file sehat
        preflight = get_preflight()
        preflight_result = preflight.check(str(file_path))
        
        if preflight_result.get("success", False):
            print(f"  ✅ File already healthy")
            healthy_count += 1
            results.append({
                "file": str(file_path.name),
                "status": "healthy",
                "time": 0,
                "success": True
            })
            total_time += time.time() - start
            continue
        
        # Jalankan pipeline
        pipeline = RepairPipeline()
        result = pipeline.run(str(file_path))
        
        elapsed = time.time() - start
        total_time += elapsed
        
        # Verify after repair
        preflight_after = preflight.check(str(file_path))
        
        success = result.get("success", False) and preflight_after.get("success", False)
        
        if success:
            repaired_count += 1
        else:
            failed_count += 1
        
        results.append({
            "file": str(file_path.name),
            "status": "repaired" if success else "failed",
            "success": success,
            "pipeline_success": result.get("success", False),
            "preflight_after": preflight_after.get("success", False),
            "attempts": result.get("attempts", 0),
            "time": elapsed,
            "errors": preflight_result.get("errors", [])
        })
        
        print(f"  {'✅' if success else '❌'} Success: {success}")
        print(f"  ⏱ Time: {elapsed:.2f}s")
    
    # Summary
    print("\n" + "="*60)
    print("REAL-WORLD TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    
    print(f"Total files tested: {total}")
    print(f"Already healthy: {healthy_count}")
    print(f"Successfully repaired: {repaired_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {(healthy_count + repaired_count)/total*100:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Avg time: {total_time/total:.2f}s")
    
    # Save report
    report_file = Path(__file__).parent / "results" / "real_world_report.json"
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "repository": "fastapi",
        "total": total,
        "healthy": healthy_count,
        "repaired": repaired_count,
        "failed": failed_count,
        "success_rate": (healthy_count + repaired_count)/total*100,
        "total_time": total_time,
        "avg_time": total_time/total,
        "results": results
    }, indent=2))
    
    print(f"\n📄 Report saved: {report_file}")

if __name__ == "__main__":
    test_real_world()
