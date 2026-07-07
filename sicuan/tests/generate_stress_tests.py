#!/usr/bin/env python3
"""
Generate 30+ stress test fixtures untuk SiCuan
"""

import os
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures_stress"
FIXTURES_DIR.mkdir(exist_ok=True)

FIXTURES = {
    # 1. Basic syntax errors
    "01_nested_class.py": """
class Outer:
    class Inner:
        def __init__(self):
            self.value = 1
""",
    "02_decorator.py": """
def log(func):
    return func

@log
def hello():
    print("hello")
""",
    "03_async_function.py": """
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "data"
""",
    "04_inheritance.py": """
class Base:
    def method(self):
        return "base"

class Child(Base):
    def method(self):
        return super().method() + " child"
""",
    "05_abstract_class.py": """
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def doit(self):
        pass
""",
    "06_dataclass.py": """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
""",
    "07_enum.py": """
from enum import Enum

class Color(Enum):
    RED = 1
    BLUE = 2
""",
    "08_property.py": """
class Person:
    def __init__(self):
        self._name = ""
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
""",
    "09_import_alias.py": """
import os as operating_system
from datetime import datetime as dt
""",
    "10_circular_import.py": """
# Simulasi circular import
# Ini akan dipisah ke dua file
""",
    "11_multiple_syntax_error.py": """
class Strategy:
    def run(self)
        print("hello"
    
    def stop(self:
        pass
""",
    "12_broken_docstring.py": """
class Strategy:
    def run(self):
        \"""This docstring is broken
        pass
""",
    "13_mixed_tabs_spaces.py": """
class Strategy:
\tdef run(self):
\t    print("tab")
        print("space")
""",
    "14_generic_typing.py": """
from typing import List, Dict, Optional

def process(data: List[Dict[str, Optional[int]]]) -> None:
    pass
""",
    "15_overload.py": """
from typing import overload

class Calculator:
    @overload
    def add(self, a: int, b: int) -> int:
        pass
""",
    "16_large_file.py": """
# File >3000 lines - akan dibuat terpisah
""",
    "17_multi_file.py": """
# Multi-file repair - akan dibuat terpisah
""",
    "18_runtime_exception.py": """
class Strategy:
    def run(self):
        raise RuntimeError("Something went wrong")
""",
}

# Generate fixtures
for name, content in FIXTURES.items():
    file_path = FIXTURES_DIR / name
    file_path.write_text(content)
    print(f"✅ Created {name}")

print(f"\n📁 Generated {len(FIXTURES)} test fixtures in {FIXTURES_DIR}")
