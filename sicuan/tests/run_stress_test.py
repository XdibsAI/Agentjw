#!/usr/bin/env python3
"""Stress Test Runner - 30+ test cases"""

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.core.repair_pipeline import RepairPipeline
from sicuan.core.preflight import get_preflight

def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]

def test_fixture(fixture_path, name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"File: {fixture_path}")
    
    hash_before = hash_file(fixture_path)
    start = time.time()
    
    pipeline = RepairPipeline()
    result = pipeline.run(str(fixture_path))
    
    elapsed = time.time() - start
    hash_after = hash_file(fixture_path)
    
    preflight = get_preflight()
    preflight_result = preflight.check(str(fixture_path))
    
    passed = result['success'] and preflight_result['success']
    
    print(f"✅ PASS" if passed else "❌ FAIL")
    print(f"  - Pipeline success: {result['success']}")
    print(f"  - Preflight success: {preflight_result['success']}")
    print(f"  - Attempts: {result['attempts']}")
    print(f"  - Hash changed: {hash_before != hash_after}")
    print(f"  - Time: {elapsed:.2f}s")
    
    return {
        "name": name,
        "passed": passed,
        "pipeline_success": result['success'],
        "preflight_success": preflight_result['success'],
        "attempts": result['attempts'],
        "hash_changed": hash_before != hash_after,
        "time": elapsed,
        "errors": preflight_result.get('errors', [])
    }

def main():
    fixtures_dir = Path(__file__).parent / "fixtures_stress"
    temp_dir = Path(__file__).parent / "temp_stress"
    temp_dir.mkdir(exist_ok=True)
    
    fixtures = sorted(fixtures_dir.glob("*.py"))
    results = []
    
    for fixture in fixtures:
        dst = temp_dir / fixture.name
        dst.write_text(fixture.read_text())
        result = test_fixture(dst, fixture.stem)
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("STRESS TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass Rate: {passed/total*100:.1f}%")
    
    # Save report
    report_file = Path(__file__).parent / "results" / "stress_report.json"
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed/total*100,
        "results": results
    }, indent=2))
    
    print(f"\n📄 Report saved: {report_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
