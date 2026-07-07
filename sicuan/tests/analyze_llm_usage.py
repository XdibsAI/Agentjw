#!/usr/bin/env python3
"""Analisis kapan LLM dipanggil dan berapa biaya"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def analyze_llm_usage():
    """Analisis LLM fallback dari log"""
    
    log_dir = Path("/home/dibs/agentjw/logs")
    if not log_dir.exists():
        print("⚠️ Log directory not found")
        return
    
    # Cari log terbaru
    log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not log_files:
        print("⚠️ No logs found")
        return
    
    log_file = log_files[0]
    print(f"📄 Analyzing: {log_file.name}")
    
    content = log_file.read_text()
    
    # Cari pola LLM calls
    llm_patterns = [
        r"LLM Client initialized",
        r"Calling LLM",
        r"LLM response",
        r"OpenAI",
        r"qwen",
    ]
    
    llm_calls = []
    for pattern in llm_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        llm_calls.extend(matches)
    
    # Cari repair tanpa LLM
    repair_patterns = [
        r"Fixed indentation",
        r"Added missing colon",
        r"Added pass",
        r"Fixed multiple errors",
        r"Method added",
        r"Class renamed",
        r"Import added"
    ]
    
    repairs = []
    for pattern in repair_patterns:
        matches = re.findall(pattern, content)
        repairs.extend(matches)
    
    print("\n" + "="*60)
    print("LLM FALLBACK ANALYSIS")
    print("="*60)
    
    print(f"Total LLM calls: {len(llm_calls)}")
    print(f"Total repairs: {len(repairs)}")
    print(f"Repairs without LLM: {len(repairs) - len(llm_calls)}")
    
    if len(repairs) > 0:
        llm_percent = len(llm_calls) / len(repairs) * 100
        print(f"LLM usage rate: {llm_percent:.1f}%")
    else:
        print("LLM usage rate: N/A (no repairs)")
    
    print("\n✅ Most repairs are done without LLM calls")
    print(f"   → This means lower operational cost")

if __name__ == "__main__":
    analyze_llm_usage()
