#!/usr/bin/env python3
"""Benchmark performance dan scalability"""

import time
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.core.repair_pipeline import RepairPipeline
from sicuan.core.preflight import get_preflight


def benchmark_file(file_path):
    """Benchmark satu file"""
    start = time.time()
    
    pipeline = RepairPipeline()
    result = pipeline.run(str(file_path))
    
    elapsed = time.time() - start
    
    return {
        "file": str(file_path),
        "time": elapsed,
        "attempts": result['attempts'],
        "success": result['success'],
        "stages": len(result.get('stages', []))
    }


def run_benchmark():
    """Run benchmark on all fixtures"""
    fixtures_dir = Path(__file__).parent / "temp_stress"
    results = []
    
    for fixture in sorted(fixtures_dir.glob("*.py")):
        result = benchmark_file(fixture)
        results.append(result)
        print(f"{fixture.name:30} {result['time']:.3f}s  attempts={result['attempts']} success={result['success']}")
    
    # Summary
    total = len(results)
    success = sum(1 for r in results if r['success'])
    total_time = sum(r['time'] for r in results)
    avg_time = total_time / total if total > 0 else 0
    
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(f"Total files: {total}")
    print(f"Success rate: {success/total*100:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time: {avg_time:.2f}s")
    print(f"Max time: {max(r['time'] for r in results):.2f}s")
    print(f"Min time: {min(r['time'] for r in results):.2f}s")
    
    # Save report
    report_file = Path(__file__).parent / "results" / "benchmark_report.json"
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "success": success,
        "success_rate": success/total*100,
        "total_time": total_time,
        "avg_time": avg_time,
        "max_time": max(r['time'] for r in results),
        "min_time": min(r['time'] for r in results),
        "results": results
    }, indent=2))
    
    print(f"\n📄 Report saved: {report_file}")

if __name__ == "__main__":
    run_benchmark()
