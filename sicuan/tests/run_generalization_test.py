#!/usr/bin/env python3
"""Test generalisasi SiCuan pada berbagai struktur proyek Python"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.core.repair_pipeline import RepairPipeline


def test_generalization():
    """Test pada berbagai struktur Python"""
    
    test_cases = [
        {
            "name": "FastAPI-style (no class)",
            "code": """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "hello"}
""",
            "expected": True
        },
        {
            "name": "Flask-style (decorators)",
            "code": """
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "hello"
""",
            "expected": True
        },
        {
            "name": "CLI-style (functions only)",
            "code": """
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name")
    args = parser.parse_args()
    print(f"Hello {args.name}")

if __name__ == "__main__":
    main()
""",
            "expected": True
        },
        {
            "name": "Class without Strategy",
            "code": """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def sub(self, a, b):
        return a - b
""",
            "expected": True
        },
        {
            "name": "Mixed functions and classes",
            "code": """
def helper():
    return True

class Processor:
    def process(self, data):
        return helper() and data
""",
            "expected": True
        }
    ]
    
    passed = 0
    failed = 0
    
    print("="*60)
    print("GENERALIZATION TEST")
    print("="*60)
    
    for case in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(case["code"])
            temp_file = f.name
        
        # Jalankan pipeline
        pipeline = RepairPipeline()
        result = pipeline.run(temp_file)
        
        success = result.get("success", False)
        status = "✅ PASS" if success else "❌ FAIL"
        
        if success == case["expected"]:
            passed += 1
            print(f"{status} - {case['name']}")
        else:
            failed += 1
            print(f"{status} - {case['name']} (expected {case['expected']})")
        
        Path(temp_file).unlink()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {passed/(passed+failed)*100:.1f}%")

if __name__ == "__main__":
    test_generalization()
