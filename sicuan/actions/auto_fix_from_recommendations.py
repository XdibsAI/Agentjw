"""
auto_fix_from_recommendations - Perbaiki otomatis berdasarkan rekomendasi analisis
"""

import sqlite3
import re
from pathlib import Path
from typing import Dict, List


def execute(task: dict) -> dict:
    """Auto-fix berdasarkan rekomendasi dari analyze_project"""
    project = task.get("target", "godmeme")
    recommendations = task.get("recommendations", [])
    
    if not recommendations:
        return {
            "success": False,
            "summary": "Tidak ada rekomendasi untuk diperbaiki",
            "data": {}
        }
    
    fixes = []
    errors = []
    applied_fixes = set()
    
    for rec in recommendations:
        if "Turunkan score threshold" in rec or "score threshold" in rec:
            if "Score threshold" not in applied_fixes:
                result = _fix_score_threshold()
                fixes.append(result)
                applied_fixes.add("Score threshold")
        elif "Periksa kondisi _should_buy" in rec or "should_buy" in rec:
            if "should_buy" not in applied_fixes:
                result = _fix_should_buy()
                fixes.append(result)
                applied_fixes.add("should_buy")
        elif "Naikkan daily loss limit" in rec or "daily loss" in rec:
            if "daily loss" not in applied_fixes:
                result = _fix_daily_loss_limit()
                fixes.append(result)
                applied_fixes.add("daily loss")
        elif "Win rate rendah" in rec or "win rate" in rec:
            if "win rate" not in applied_fixes:
                result = _fix_win_rate()
                fixes.append(result)
                applied_fixes.add("win rate")
        elif "Bot hanya SELL" in rec or "tidak ada BUY" in rec:
            if "BUY logic" not in applied_fixes:
                result = _fix_buy_logic()
                fixes.append(result)
                applied_fixes.add("BUY logic")
        elif "Total PnL negatif" in rec or "PnL negatif" in rec:
            if "PnL" not in applied_fixes:
                result = _fix_pnl()
                fixes.append(result)
                applied_fixes.add("PnL")
        else:
            errors.append(f"Tidak ada fix untuk: {rec[:50]}...")
    
    return {
        "success": len(errors) == 0,
        "summary": f"Applied {len(fixes)} fixes, {len(errors)} errors",
        "data": {
            "fixes": fixes,
            "errors": errors
        }
    }


def _fix_score_threshold() -> Dict:
    """Fix: turunkan score threshold di strategy.py"""
    try:
        strategy_file = Path("projects/godmeme_bot/strategy.py")
        if not strategy_file.exists():
            return {"status": "error", "message": "File not found"}
        
        content = strategy_file.read_text()
        
        if "should = score >=" in content:
            new_content = re.sub(
                r'should = score >= \d+',
                'should = score >= 8',
                content
            )
            strategy_file.write_text(new_content)
            return {"status": "success", "message": "Score threshold diturunkan dari 10 ke 8"}
        else:
            return {"status": "error", "message": "Score threshold not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fix_should_buy() -> Dict:
    """Fix: tambahkan log di _should_buy"""
    try:
        strategy_file = Path("projects/godmeme_bot/strategy.py")
        if not strategy_file.exists():
            return {"status": "error", "message": "File not found"}
        
        content = strategy_file.read_text()
        
        if "logger.info(f\"BUY signal" in content:
            return {"status": "info", "message": "Log sudah ada di _should_buy"}
        
        new_content = re.sub(
            r'(return should)',
            r'        logger.info(f"BUY DECISION: {token.get(\"symbol\")} | score={score} | should={should}")\n        \1',
            content
        )
        strategy_file.write_text(new_content)
        return {"status": "success", "message": "Logging ditambahkan di _should_buy"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fix_daily_loss_limit() -> Dict:
    """Fix: naikkan daily loss limit"""
    try:
        strategy_file = Path("projects/godmeme_bot/strategy.py")
        if not strategy_file.exists():
            return {"status": "error", "message": "File not found"}
        
        content = strategy_file.read_text()
        
        if "MAX_DAILY_LOSS_SOL" not in content:
            return {"status": "error", "message": "MAX_DAILY_LOSS_SOL not found"}
        
        new_content = re.sub(
            r'MAX_DAILY_LOSS_SOL = [\d.]+',
            'MAX_DAILY_LOSS_SOL = 0.5',
            content
        )
        strategy_file.write_text(new_content)
        return {"status": "success", "message": "Daily loss limit dinaikkan ke 0.5 SOL"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fix_win_rate() -> Dict:
    """Fix: turunkan target win rate atau adjust strategy"""
    try:
        # Turunkan score threshold juga membantu win rate
        result = _fix_score_threshold()
        if result["status"] == "success":
            return {"status": "success", "message": "Win rate diperbaiki dengan menurunkan score threshold"}
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fix_buy_logic() -> Dict:
    """Fix: perbaiki logika BUY"""
    try:
        strategy_file = Path("projects/godmeme_bot/strategy.py")
        if not strategy_file.exists():
            return {"status": "error", "message": "File not found"}
        
        content = strategy_file.read_text()
        
        # Cek apakah ada BUY logic
        if "BUY" in content:
            # Tambahkan logging untuk melihat kenapa tidak ada BUY
            new_content = re.sub(
                r'(return False)',
                r'        logger.info(f"BUY REJECTED: {token.get(\"symbol\")} | reason: condition not met")\n        \1',
                content
            )
            strategy_file.write_text(new_content)
            return {"status": "success", "message": "Logging ditambahkan untuk debug BUY logic"}
        else:
            return {"status": "error", "message": "BUY logic not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fix_pnl() -> Dict:
    """Fix: perbaiki PnL dengan adjust strategi"""
    try:
        # Kombinasi fix: score threshold + daily loss
        results = []
        
        # 1. Turunkan threshold
        r1 = _fix_score_threshold()
        results.append(r1)
        
        # 2. Naikkan daily loss limit
        r2 = _fix_daily_loss_limit()
        results.append(r2)
        
        success_count = sum(1 for r in results if r["status"] == "success")
        
        return {
            "status": "success" if success_count > 0 else "error",
            "message": f"PnL diperbaiki dengan {success_count} perubahan (threshold + daily loss)"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
