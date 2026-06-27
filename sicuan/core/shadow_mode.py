"""
Shadow Mode - Bandingkan Executive Brain vs Legacy
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from core.logger import logger
from sicuan.core.result_contract import ResultContract

ROOT = Path("/home/dibs/agentjw")
SHADOW_LOG = ROOT / "memory" / "shadow_mode.log"
SHADOW_REPORT = ROOT / "memory" / "shadow_report.json"


class ShadowMode:
    """
    Shadow Mode - jalankan Executive Brain dan Legacy paralel.
    Bandingkan hasil, catat perbedaan, tidak memengaruhi produksi.
    """
    
    def __init__(self):
        self.results: List[Dict] = []
        self.matches = 0
        self.mismatches = 0
        self.executive_only = 0
        self.legacy_only = 0
        self._load_report()
    
    def _load_report(self):
        """Load report dari file"""
        if SHADOW_REPORT.exists():
            try:
                data = json.loads(SHADOW_REPORT.read_text())
                self.results = data.get("results", [])
                self.matches = data.get("matches", 0)
                self.mismatches = data.get("mismatches", 0)
                self.executive_only = data.get("executive_only", 0)
                self.legacy_only = data.get("legacy_only", 0)
            except:
                pass
    
    def _save_report(self):
        """Save report ke file"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": self.results[-100:],  # Keep last 100
            "matches": self.matches,
            "mismatches": self.mismatches,
            "executive_only": self.executive_only,
            "legacy_only": self.legacy_only,
            "total": self.matches + self.mismatches + self.executive_only + self.legacy_only
        }
        SHADOW_REPORT.write_text(json.dumps(report, indent=2, default=str))
    
    def _log(self, message: str):
        """Log ke file"""
        timestamp = datetime.utcnow().isoformat()
        with open(SHADOW_LOG, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def run(self, brain, action: str, target: str, user_request: str, session_id: str = "shadow") -> Dict:
        """
        Jalankan action di Executive Brain dan Legacy, bandingkan hasil.
        """
        logger.info(f"Shadow Mode: {action} -> {target}")
        
        result = {
            "action": action,
            "target": target,
            "user_request": user_request[:100],
            "timestamp": datetime.utcnow().isoformat(),
            "executive": {"success": False, "result": "", "duration": 0, "error": None},
            "legacy": {"success": False, "result": "", "duration": 0, "error": None},
            "match": False,
            "status": "unknown"
        }
        
        # === Executive Brain ===
        try:
            start = time.time()
            exec_result = brain.execute_action(action, target, user_request, f"{session_id}_exec")
            exec_duration = time.time() - start
            result["executive"]["success"] = bool(exec_result)
            result["executive"]["result"] = str(exec_result)[:500]
            result["executive"]["duration"] = exec_duration
        except Exception as e:
            result["executive"]["error"] = str(e)
            result["executive"]["success"] = False
        
        # === Legacy (IF-ELIF) ===
        try:
            start = time.time()
            legacy_result = brain.execute_action_legacy(action, target, user_request, f"{session_id}_legacy")
            legacy_duration = time.time() - start
            result["legacy"]["success"] = bool(legacy_result)
            result["legacy"]["result"] = str(legacy_result)[:500]
            result["legacy"]["duration"] = legacy_duration
        except Exception as e:
            result["legacy"]["error"] = str(e)
            result["legacy"]["success"] = False
        
        
        # === BANDINGKAN DENGAN RESULT CONTRACT ===
        exec_success = result["executive"]["success"]
        legacy_success = result["legacy"]["success"]
        exec_result_str = result["executive"]["result"][:500]
        legacy_result_str = result["legacy"]["result"][:500]
        
        # Buat contract dari raw result
        action = result.get("action", "unknown")
        target = result.get("target", "")
        
        # Coba parse sebagai contract
        exec_result = result["executive"]["result"]
        legacy_result = result["legacy"]["result"]
        
        # Jika result adalah JSON string, parse
        import json
        try:
            exec_dict = json.loads(exec_result) if isinstance(exec_result, str) else exec_result
            if isinstance(exec_dict, dict) and "success" in exec_dict and "action" in exec_dict:
                exec_contract = ResultContract.from_dict(exec_dict)
            else:
                exec_contract = ResultContract.from_raw(
                    action=action,
                    entity=target,
                    result={"success": exec_success, "display": exec_result_str, "data": {}},
                    duration=result["executive"]["duration"]
                )
        except:
            exec_contract = ResultContract.from_raw(
                action=action,
                entity=target,
                result={"success": exec_success, "display": exec_result_str, "data": {}},
                duration=result["executive"]["duration"]
            )
        
        try:
            legacy_dict = json.loads(legacy_result) if isinstance(legacy_result, str) else legacy_result
            if isinstance(legacy_dict, dict) and "success" in legacy_dict and "action" in legacy_dict:
                legacy_contract = ResultContract.from_dict(legacy_dict)
            else:
                legacy_contract = ResultContract.from_raw(
                    action=action,
                    entity=target,
                    result={"success": legacy_success, "display": legacy_result_str, "data": {}},
                    duration=result["legacy"]["duration"]
                )
        except:
            legacy_contract = ResultContract.from_raw(
                action=action,
                entity=target,
                result={"success": legacy_success, "display": legacy_result_str, "data": {}},
                duration=result["legacy"]["duration"]
            )
        
        # Compare contracts
        comparison = exec_contract.compare(legacy_contract)
        is_match = comparison.get("match", False)
        
        result["match"] = is_match
        result["success_match"] = comparison.get("success_match", False)
        result["action_match"] = comparison.get("action_match", False)
        result["entity_match"] = comparison.get("entity_match", False)
        result["metrics_match"] = comparison.get("metrics_match", False)
        result["differences"] = comparison.get("differences", [])
        result["status"] = "match" if is_match else "mismatch"
# Update stats
        if is_match:
            self.matches += 1
        else:
            self.mismatches += 1
            self._log(f"MISMATCH: {action} -> {target}")
            self._log(f"  Exec: {exec_result_str[:100]}")
            self._log(f"  Legacy: {legacy_result_str[:100]}")
        
        # Simpan result
        self.results.append(result)
        if len(self.results) > 100:
            self.results = self.results[-100:]
        
        self._save_report()
        
        return result
    
    def summary(self) -> Dict:
        """Dapatkan ringkasan Shadow Mode"""
        total = self.matches + self.mismatches + self.executive_only + self.legacy_only
        
        # Hitung match rate per action
        action_stats = defaultdict(lambda: {"total": 0, "matches": 0})
        for r in self.results:
            action = r.get("action", "unknown")
            action_stats[action]["total"] += 1
            if r.get("match", False):
                action_stats[action]["matches"] += 1
        
        action_rates = {}
        for action, stats in action_stats.items():
            rate = (stats["matches"] / stats["total"] * 100) if stats["total"] > 0 else 0
            action_rates[action] = {"total": stats["total"], "matches": stats["matches"], "rate": rate}
        
        return {
            "total": total,
            "matches": self.matches,
            "mismatches": self.mismatches,
            "executive_only": self.executive_only,
            "legacy_only": self.legacy_only,
            "match_rate": (self.matches / total * 100) if total > 0 else 0,
            "action_rates": action_rates,
            "last_results": self.results[-10:]
        }
    
    def print_summary(self):
        """Print ringkasan ke console"""
        summary = self.summary()
        
        print("\n" + "=" * 60)
        print("🔦 SHADOW MODE SUMMARY")
        print("=" * 60)
        print(f"Total comparisons : {summary['total']}")
        print(f"Matches          : {summary['matches']}")
        print(f"Mismatches       : {summary['mismatches']}")
        print(f"Match rate       : {summary['match_rate']:.1f}%")
        
        if summary['action_rates']:
            print("\n📊 Per Action:")
            for action, stats in sorted(summary['action_rates'].items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
                status = "✅" if stats['rate'] == 100 else "⚠️" if stats['rate'] > 80 else "❌"
                print(f"  {status} {action}: {stats['matches']}/{stats['total']} ({stats['rate']:.0f}%)")
        
        if summary['last_results']:
            print("\n📋 Last 5 comparisons:")
            for r in summary['last_results'][-5:]:
                status = "✅" if r.get('match') else "❌"
                print(f"  {status} {r.get('action')} -> {r.get('target')}")
        
        print("=" * 60)
    
    def export_report(self) -> str:
        """Export report ke string JSON"""
        return json.dumps(self.summary(), indent=2, default=str)


# Singleton instance
_shadow = None

def get_shadow() -> ShadowMode:
    global _shadow
    if _shadow is None:
        _shadow = ShadowMode()
    return _shadow
