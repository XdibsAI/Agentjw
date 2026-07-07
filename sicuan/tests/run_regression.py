#!/usr/bin/env python3
"""Regression Test - RepairPipeline on broken files"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.core.repair_pipeline import RepairPipeline
from sicuan.core.preflight import get_preflight


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]

def test_file(fixture_path, description):
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"File: {fixture_path}")
    print(f"{'='*60}")
    
    # Hash before
    hash_before = hash_file(fixture_path)
    print(f"Hash before: {hash_before}")
    
    # Run pipeline
    pipeline = RepairPipeline()
    result = pipeline.run(str(fixture_path))
    
    # Hash after
    hash_after = hash_file(fixture_path)
    print(f"Hash after: {hash_after}")
    
    # Preflight after
    preflight = get_preflight()
    preflight_result = preflight.check(str(fixture_path))
    
    # Results
    print(f"Pipeline Success: {result['success']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Hash changed: {hash_before != hash_after}")
    print(f"Preflight Success: {preflight_result['success']}")
    print(f"Errors: {preflight_result.get('errors', [])}")
    
    return {
        "file": str(fixture_path),
        "description": description,
        "pipeline_success": result['success'],
        "attempts": result['attempts'],
        "hash_changed": hash_before != hash_after,
        "preflight_success": preflight_result['success'],
        "errors": preflight_result.get('errors', [])
    }


def main():
    fixtures_dir = Path(__file__).parent / "fixtures"
    results = []
    
    # Copy fixtures to temp directory (so we don't modify original)
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # Test each fixture
    fixtures = [
        ("missing_method.py", "Missing method _check_cooldown"),
        ("syntax_error.py", "Indentation error"),
        ("missing_import.py", "Missing import List"),
        ("duplicate_method.py", "Duplicate method"),
        ("broken_class.py", "Wrong class name"),
        ("healthy.py", "Already healthy file")
    ]
    
    for fixture_name, desc in fixtures:
        src = fixtures_dir / fixture_name
        if not src.exists():
            print(f"⚠️ Skipping {fixture_name} - not found")
            continue
        
        # Copy to temp
        dst = temp_dir / fixture_name
        dst.write_text(src.read_text())
        
        # Test
        result = test_file(dst, desc)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("REGRESSION TEST SUMMARY")
    print(f"{'='*60}")
    
    total = len(results)
    passed = sum(1 for r in results if r['pipeline_success'] and r['preflight_success'])
    
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    for r in results:
        status = "✅ PASS" if (r['pipeline_success'] and r['preflight_success']) else "❌ FAIL"
        print(f"  {status} - {r['description']} (attempts: {r['attempts']})")
        if r['errors']:
            print(f"    Errors: {r['errors']}")
    
    # Save results
    report_file = Path(__file__).parent / "results" / "regression_report.json"
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {"total": total, "passed": passed, "failed": total - passed}
    }, indent=2))
    
    print(f"\n📄 Report saved: {report_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
