"""
Self-Review berbasis data - evaluasi SiCuan dari metrik nyata
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class SelfReviewData:
    """Generate self-review dari data aktual, bukan opini LLM"""

    def __init__(self):
        self.memory_dir = Path("memory")
        self.report = {}

    def generate(self) -> Dict[str, Any]:
        """Generate self-review report dari semua sumber data"""
        
        # 1. Load data dari berbagai sumber
        doctor = self._load_doctor()
        shadow = self._load_shadow()
        runtime = self._load_runtime()
        reflection = self._load_reflection()
        regression = self._load_regression()
        provenance = self._load_provenance()
        
        # 2. Compile metrics
        metrics = {
            "workflow_success_rate": runtime.get("success_rate", 0),
            "regression_pass": regression.get("pass", "0/0"),
            "shadow_match_rate": shadow.get("match_rate", 0),
            "avg_confidence": reflection.get("avg_confidence", 0),
            "retry_rate": reflection.get("retry_rate", 0),
            "health_score": doctor.get("health_score", 0),
            "total_provenance_records": provenance.get("total", 0),
            "active_goals": len(self._get_goals()),
        }
        
        # 3. Detect issues
        issues = self._detect_issues(metrics, doctor, shadow)
        
        # 4. Generate recommendations
        recommendations = self._generate_recommendations(metrics, issues)
        
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "issues": issues,
            "recommendations": recommendations,
            "summary": self._generate_summary(metrics, issues)
        }
        
        return self.report

    def _load_doctor(self) -> Dict:
        """Load data dari Doctor Dashboard"""
        doctor_file = self.memory_dir / "doctor_report.json"
        if doctor_file.exists():
            try:
                return json.loads(doctor_file.read_text())
            except:
                pass
        return {"health_score": 100, "services": {}}

    def _load_shadow(self) -> Dict:
        """Load data dari Shadow Mode"""
        shadow_file = self.memory_dir / "shadow_report.json"
        if shadow_file.exists():
            try:
                data = json.loads(shadow_file.read_text())
                total = data.get("total", 0)
                matches = data.get("matches", 0)
                return {
                    "match_rate": (matches / total * 100) if total > 0 else 0,
                    "total": total,
                    "matches": matches,
                    "mismatches": data.get("mismatches", 0),
                }
            except:
                pass
        return {"match_rate": 0, "total": 0}

    def _load_runtime(self) -> Dict:
        """Load data dari Runtime Bus"""
        runtime_file = self.memory_dir / "runtime_state.json"
        if runtime_file.exists():
            try:
                data = json.loads(runtime_file.read_text())
                return {
                    "success_rate": data.get("success_rate", 0),
                    "total_executions": data.get("total_executions", 0),
                    "avg_duration": data.get("avg_duration", 0),
                }
            except:
                pass
        return {"success_rate": 0, "total_executions": 0}

    def _load_reflection(self) -> Dict:
        """Load data dari Reflection Engine"""
        reflection_file = self.memory_dir / "reflection_log.json"
        if reflection_file.exists():
            try:
                data = json.loads(reflection_file.read_text())
                if data:
                    confidences = [r.get("confidence", 0) for r in data]
                    retries = [r for r in data if r.get("next_action") == "retry"]
                    return {
                        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                        "retry_rate": (len(retries) / len(data) * 100) if data else 0,
                        "total_reflections": len(data),
                    }
            except:
                pass
        return {"avg_confidence": 0, "retry_rate": 0}

    def _load_regression(self) -> Dict:
        """Load data dari Regression Suite"""
        regression_file = self.memory_dir / "regression_report.json"
        if regression_file.exists():
            try:
                data = json.loads(regression_file.read_text())
                return {
                    "pass": f"{data.get('passed', 0)}/{data.get('total', 0)}",
                    "passed": data.get('passed', 0),
                    "total": data.get('total', 0),
                }
            except:
                pass
        return {"pass": "0/0", "passed": 0, "total": 0}

    def _load_provenance(self) -> Dict:
        """Load data dari Provenance Engine"""
        prov_file = self.memory_dir / "provenance_records.json"
        if prov_file.exists():
            try:
                data = json.loads(prov_file.read_text())
                records = data.get("records", [])
                return {"total": len(records)}
            except:
                pass
        return {"total": 0}

    def _get_goals(self) -> List:
        """Load active goals"""
        goals_file = self.memory_dir / "goals_engine.json"
        if goals_file.exists():
            try:
                data = json.loads(goals_file.read_text())
                goals = data.get("goals", {})
                return [g for g in goals.values() if g.get("status") != "completed"]
            except:
                pass
        return []

    def _detect_issues(self, metrics: Dict, doctor: Dict, shadow: Dict) -> List[str]:
        """Deteksi masalah dari data"""
        issues = []
        
        # Latency (dari doctor)
        if doctor.get("avg_latency", 0) > 15:
            issues.append("Latency masih tinggi (15-40 detik) - pertimbangkan model berbayar")
        
        # HTTP 429
        if doctor.get("http_429_count", 0) > 5:
            issues.append(f"HTTP 429 terjadi {doctor.get('http_429_count')} kali - rate limit")
        
        # Shadow mode mismatch
        if shadow.get("match_rate", 100) < 70:
            issues.append(f"Shadow mode match rate rendah ({shadow.get('match_rate')}%)")
        
        # Retry rate
        if metrics.get("retry_rate", 0) > 10:
            issues.append(f"Retry rate {metrics.get('retry_rate')}% - perlu investigasi")
        
        # Auto-learning
        if not (self.memory_dir / "learning_log.json").exists():
            issues.append("Belum ada auto-learning - planner tidak update otomatis")
        
        # Drift monitoring
        if not (self.memory_dir / "drift_report.json").exists():
            issues.append("Belum ada drift monitoring - performa bot tidak terpantau")
        
        return issues

    def _generate_recommendations(self, metrics: Dict, issues: List) -> List[str]:
        """Generate rekomendasi dari issues"""
        recommendations = []
        
        if "Latency" in "\n".join(issues):
            recommendations.append("Optimasi latency dengan model berbayar (GPT-4o/Claude)")
        
        if "HTTP 429" in "\n".join(issues):
            recommendations.append("Implementasi retry mechanism dengan exponential backoff")
        
        if "Shadow mode" in "\n".join(issues):
            recommendations.append("Audit Shadow Mode - cari penyebab mismatch")
        
        if "Retry rate" in "\n".join(issues):
            recommendations.append("Investigasi retry rate - cek Reflection Engine")
        
        if "auto-learning" in "\n".join(issues):
            recommendations.append("Implementasi auto-learning scheduler untuk planner update")
        
        if "drift monitoring" in "\n".join(issues):
            recommendations.append("Buat drift monitoring untuk performa bot")
        
        if not recommendations:
            recommendations.append("Semua sistem berjalan baik! Lanjutkan monitoring.")
        
        return recommendations

    def _generate_summary(self, metrics: Dict, issues: List) -> str:
        """Generate summary naratif dari data"""
        health = metrics.get("health_score", 0)
        success = metrics.get("workflow_success_rate", 0)
        shadow = metrics.get("shadow_match_rate", 0)
        
        if health >= 90 and success >= 95 and shadow >= 80:
            return "✅ Sistem dalam kondisi sangat baik! Semua metrik menunjukkan performa optimal."
        elif health >= 70 and success >= 80:
            return "⚠️ Sistem berjalan dengan baik, ada beberapa area yang perlu ditingkatkan."
        else:
            return "🔴 Perlu perhatian! Beberapa metrik di bawah threshold yang diharapkan."

    def print_report(self):
        """Print report ke console"""
        report = self.generate()
        
        print("\n" + "=" * 60)
        print("📊 SELF-REVIEW SICUAN - BERBASIS DATA")
        print("=" * 60)
        print(f"Timestamp: {report['timestamp']}")
        
        print("\n📈 METRICS:")
        for key, value in report['metrics'].items():
            print(f"  {key}: {value}")
        
        if report['issues']:
            print("\n⚠️ ISSUES DETEKSI:")
            for issue in report['issues']:
                print(f"  • {issue}")
        else:
            print("\n✅ Tidak ada issues terdeteksi!")
        
        if report['recommendations']:
            print("\n💡 REKOMENDASI:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        print("\n📝 SUMMARY:")
        print(f"  {report['summary']}")
        print("=" * 60)
        
        return report

# Singleton
_review = None

def get_self_review():
    global _review
    if _review is None:
        _review = SelfReviewData()
    return _review
