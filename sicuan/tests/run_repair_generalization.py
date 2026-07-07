#!/usr/bin/env python3
"""Test generalisasi repair pada berbagai proyek Python yang sengaja dirusak"""

import sys
import tempfile
import ast
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.core.repair_pipeline import RepairPipeline


def test_repair_generalization():
    """Test repair pada berbagai struktur Python yang dirusak"""

    test_cases = [
        {
            "name": "FastAPI - missing closing paren",
            "code": """
from fastapi import FastAPI

app = FastAPI(

@app.get("/")
def hello():
    return {"message": "hello"}
""",
            "validate": lambda c: "FastAPI()" in c or "app = FastAPI()" in c,
            "expected_status": "pass"
        },
        {
            "name": "Flask - missing colon",
            "code": """
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello()
    return "hello"
""",
            "validate": lambda c: "def hello():" in c,
            "expected_status": "pass"
        },
        {
            "name": "CLI - missing closing paren",
            "code": """
import argparse

def main():
    parser = argparse.ArgumentParser(
    parser.add_argument("--name")
    args = parser.parse_args()
    print(f"Hello {args.name}")

if __name__ == "__main__":
    main()
""",
            "validate": lambda c: "ArgumentParser()" in c,
            "expected_status": "pass"
        },
        {
            "name": "Class - missing colon",
            "code": """
class Calculator
    def add(self, a, b):
        return a + b
""",
            "validate": lambda c: "class Calculator" in c and "def add" in c,
            "expected_status": "pass"
        },
        {
            "name": "Enum - broken docstring",
            "code": """
from enum import Enum

class Color(Enum):
    RED = 1
    BLUE = 2
    \"\"\"This docstring is broken
    GREEN = 3
""",
            "validate": lambda c: c.count('"""') % 2 == 0,
            "expected_status": "pass"
        },
        {
            "name": "Async - missing colon",
            "code": """
import asyncio

async def fetch_data()
    await asyncio.sleep(1)
    return "data"
""",
            "validate": lambda c: "async def fetch_data():" in c,
            "expected_status": "pass"
        },
        {
            "name": "Import - missing dependency",
            "code": """
import xyz_non_existent_module_123456

def run():
    return True
""",
            "validate": lambda c: "import xyz_non_existent_module_123456" in c,
            "expected_status": "expected"
        }
    ]

    passed = 0
    expected_count = 0
    failed = 0
    details = []

    print("="*70)
    print("REPAIR GENERALIZATION TEST")
    print("="*70)

    for case in test_cases:
        print(f"\n📝 Testing: {case['name']}")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(case["code"])
            temp_file = f.name

        # Run pipeline
        pipeline = RepairPipeline()
        result = pipeline.run(temp_file)

        # Read repaired code
        repaired = Path(temp_file).read_text()

        # Validate
        pipeline_success = result.get("success", False)
        compile_success = False
        validation_passed = False

        try:
            ast.parse(repaired)
            compile_success = True
        except SyntaxError as e:
            print(f"  ❌ Compile error: {e}")

        try:
            validation_passed = case["validate"](repaired)
        except Exception as e:
            print(f"  ❌ Validation error: {e}")

        # Determine expected status
        expected_status = case.get("expected_status", "pass")

        # Check result based on expected_status
        if expected_status == "expected":
            # Expected non-repairable: PASS if compile_success and pipeline correctly identified
            success = compile_success and not pipeline_success
            if success:
                expected_count += 1
                print(f"  🟡 EXPECTED (correctly identified as non-repairable)")
            else:
                failed += 1
                print(f"  ❌ FAIL (expected but compile failed or pipeline corrupted)")
        else:
            # Normal case: PASS if all checks pass
            success = pipeline_success and compile_success and validation_passed
            if success:
                passed += 1
                print(f"  ✅ PASS")
            else:
                failed += 1
                print(f"  ❌ FAIL")

        details.append({
            "name": case["name"],
            "success": success,
            "pipeline": pipeline_success,
            "compile": compile_success,
            "validation": validation_passed,
            "expected_status": expected_status
        })

        Path(temp_file).unlink()

    print("\n" + "="*70)
    print("REPAIR GENERALIZATION SUMMARY")
    print("="*70)
    print(f"Total: {len(test_cases)}")
    print(f"✅ PASS (repaired): {passed}")
    print(f"🟡 EXPECTED (non-repairable): {expected_count}")
    print(f"❌ FAIL (unexpected): {failed}")
    if passed + expected_count > 0:
        print(f"Success Rate: {(passed + expected_count)/(passed + expected_count + failed)*100:.1f}%")
    else:
        print(f"Success Rate: 0.0%")

    # Detail failures
    if failed > 0:
        print("\n❌ Failures:")
        for d in details:
            if not d["success"]:
                print(f"  - {d['name']}: pipeline={d['pipeline']}, compile={d['compile']}, validation={d['validation']}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(test_repair_generalization())
