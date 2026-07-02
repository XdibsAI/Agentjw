#!/usr/bin/env python3
"""
Collect production data untuk validasi Executive Brain
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

class ProductionDataCollector:
    def __init__(self):
        self.memory_dir = Path("memory")
        self.decisions_file = self.memory_dir / "executive_decisions_complete.json"
        self.workflow_history = self.memory_dir / "workflow_history.jsonl"
        
        self.decisions = []
        self.workflows = []
        self._load_data()
    
    def _load_data(self):
        """Load data dari berbagai sumber"""
        # Load decisions
        if self.decisions_file.exists():
            try:
                data = json.loads(self.decisions_file.read_text())
                self.decisions = data.get("decisions", [])
                print(f"✅ Loaded {len(self.decisions)} decisions")
            except:
                pass
        
        # Load workflows
        if self.workflow_history.exists():
            try:
                with open(self.workflow_history) as f:
                    self.workflows = [json.loads(line) for line in f]
                print(f"✅ Loaded {len(self.workflows)} workflows")
            except:
                pass
    
    def analyze_confidence_calibration(self) -> Dict:
        """Analisis kalibrasi confidence dari data nyata"""
        if not self.workflows:
            return {"status": "insufficient_data", "message": "Butuh minimal 100 workflow"}
        
        # Group by confidence bin
        bins = {
            "90-100": {"predicted": 0, "actual": 0, "count": 0},
            "80-89": {"predicted": 0, "actual": 0, "count": 0},
            "70-79": {"predicted": 0, "actual": 0, "count": 0},
            "60-69": {"predicted": 0, "actual": 0, "count": 0},
            "50-59": {"predicted": 0, "actual": 0, "count": 0},
            "<50": {"predicted": 0, "actual": 0, "count": 0},
        }
        
        for wf in self.workflows:
            conf = wf.get("confidence", 0) * 100
            success = wf.get("success", False)
            
            bin_key = self._get_bin(conf)
            if bin_key:
                bins[bin_key]["count"] += 1
                bins[bin_key]["predicted"] += conf
                if success:
                    bins[bin_key]["actual"] += 100
        
        # Hitung rata-rata per bin
        results = {}
        for key, data in bins.items():
            if data["count"] > 0:
                avg_pred = data["predicted"] / data["count"]
                avg_actual = data["actual"] / data["count"]
                error = abs(avg_pred - avg_actual)
                results[key] = {
                    "count": data["count"],
                    "predicted": avg_pred,
                    "actual": avg_actual,
                    "error": error
                }
        
        return {
            "status": "complete",
            "total_workflows": len(self.workflows),
            "bins": results,
            "calibration_quality": self._calculate_calibration_quality(results)
        }
    
    def analyze_prediction_accuracy(self) -> Dict:
        """Analisis akurasi prediksi dari data nyata"""
        if len(self.workflows) < 10:
            return {"status": "insufficient_data", "message": "Butuh minimal 10 workflow"}
        
        predictions = []
        actuals = []
        
        for wf in self.workflows:
            pred = wf.get("success_prediction", 0.5)
            success = wf.get("success", False)
            
            predictions.append(pred)
            actuals.append(1.0 if success else 0.0)
        
        error = sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)
        
        return {
            "status": "complete",
            "total": len(self.workflows),
            "avg_prediction": statistics.mean(predictions),
            "avg_actual": statistics.mean(actuals),
            "mean_absolute_error": error
        }
    
    def analyze_duration_estimation(self) -> Dict:
        """Analisis estimasi durasi dari data nyata"""
        if len(self.workflows) < 10:
            return {"status": "insufficient_data", "message": "Butuh minimal 10 workflow"}
        
        errors = []
        for wf in self.workflows:
            pred = wf.get("estimated_duration", 0)
            actual = wf.get("actual_duration", 0)
            if pred > 0 and actual > 0:
                error = abs(pred - actual) / pred * 100
                errors.append(error)
        
        if not errors:
            return {"status": "insufficient_data", "message": "Tidak ada data durasi"}
        
        return {
            "status": "complete",
            "total": len(errors),
            "avg_error": statistics.mean(errors),
            "min_error": min(errors),
            "max_error": max(errors)
        }
    
    def get_production_report(self) -> Dict:
        """Dapatkan report lengkap dari data produksi"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_decisions": len(self.decisions),
            "total_workflows": len(self.workflows),
            "confidence_calibration": self.analyze_confidence_calibration(),
            "prediction_accuracy": self.analyze_prediction_accuracy(),
            "duration_estimation": self.analyze_duration_estimation(),
        }
        
        return report
    
    def print_report(self):
        """Print report ke console"""
        report = self.get_production_report()
        
        print("\n" + "=" * 70)
        print("📊 PRODUCTION DATA ANALYSIS")
        print("=" * 70)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Decisions: {report['total_decisions']}")
        print(f"Total Workflows: {report['total_workflows']}")
        
        # Confidence Calibration
        print("\n🎯 Confidence Calibration:")
        cal = report['confidence_calibration']
        if cal['status'] == 'complete':
            for bin_key, data in cal['bins'].items():
                print(f"  {bin_key}: Pred={data['predicted']:.1f}% | Actual={data['actual']:.1f}% | Error={data['error']:.1f}%")
        else:
            print(f"  ⏳ {cal.get('message', 'Data insufficient')}")
        
        # Prediction Accuracy
        print("\n📊 Prediction Accuracy:")
        pred = report['prediction_accuracy']
        if pred['status'] == 'complete':
            print(f"  Avg Prediction: {pred['avg_prediction']:.1%}")
            print(f"  Avg Actual: {pred['avg_actual']:.1%}")
            print(f"  Mean Error: {pred['mean_absolute_error']:.1%}")
        else:
            print(f"  ⏳ {pred.get('message', 'Data insufficient')}")
        
        # Duration Estimation
        print("\n⏱️ Duration Estimation:")
        dur = report['duration_estimation']
        if dur['status'] == 'complete':
            print(f"  Avg Error: {dur['avg_error']:.1f}%")
            print(f"  Min Error: {dur['min_error']:.1f}%")
            print(f"  Max Error: {dur['max_error']:.1f}%")
        else:
            print(f"  ⏳ {dur.get('message', 'Data insufficient')}")
        
        print("=" * 70)
        
        return report
    
    def _get_bin(self, confidence: float) -> str:
        """Dapatkan bin untuk confidence"""
        if confidence >= 90:
            return "90-100"
        elif confidence >= 80:
            return "80-89"
        elif confidence >= 70:
            return "70-79"
        elif confidence >= 60:
            return "60-69"
        elif confidence >= 50:
            return "50-59"
        else:
            return "<50"
    
    def _calculate_calibration_quality(self, bins: Dict) -> str:
        """Hitung kualitas kalibrasi"""
        errors = [data["error"] for data in bins.values()]
        if not errors:
            return "insufficient"
        avg_error = statistics.mean(errors)
        if avg_error < 5:
            return "excellent"
        elif avg_error < 10:
            return "good"
        elif avg_error < 20:
            return "fair"
        else:
            return "poor"

if __name__ == "__main__":
    collector = ProductionDataCollector()
    collector.print_report()
