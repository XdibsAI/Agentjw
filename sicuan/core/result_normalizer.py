"""
Result Normalizer - Normalisasi hasil dari semua handler ke format canonical
"""

from typing import Dict, Any, Optional
from core.logger import logger


class ResultNormalizer:
    """
    Normalisasi hasil handler ke format canonical.
    Semua action harus melalui normalizer ini.
    """
    
    @staticmethod
    def normalize(action: str, target: str, result: Dict, duration: float = 0) -> Dict:
        """
        Normalisasi result ke format canonical.
        
        Args:
            action: Nama action
            target: Target action
            result: Raw result dari handler
            duration: Durasi eksekusi
        
        Returns:
            Canonical result dengan format standar
        """
        # Extract basic info
        success = result.get("success", False)
        summary = result.get("summary", "")
        data = result.get("data", {})
        error = result.get("error", "")
        errors = result.get("errors", [])
        
        # === Build display ===
        # Prioritaskan: summary > data > result string
        if summary:
            display = summary
        elif data:
            # Konversi data ke string yang readable
            if isinstance(data, dict):
                display = ResultNormalizer._dict_to_display(data, action)
            else:
                display = str(data)
        else:
            display = "✅ Task selesai" if success else f"❌ {error or 'Task gagal'}"
        
        # Jika sukses tapi tidak ada display yang jelas
        if success and (not display or display == "✅ Task selesai"):
            display = ResultNormalizer._generate_display(action, target, data)
        
        # === Confidence ===
        confidence = result.get("confidence", 0.5)
        if success:
            confidence = max(0.7, confidence)
        else:
            confidence = min(0.3, confidence)
        
        # === Build canonical result ===
        canonical = {
            "success": success,
            "display": display,
            "summary": summary or display[:200],
            "data": data,
            "confidence": confidence,
            "action": action,
            "target": target,
            "duration": duration,
            "error": error,
            "errors": errors,
            "raw": result
        }
        
        return canonical
    
    @staticmethod
    def _dict_to_display(data: Dict, action: str) -> str:
        """Konversi dict ke display string"""
        if not data:
            return "✅ Task selesai"
        
        # Untuk action tertentu, format khusus
        if action == "scan_project":
            return data.get("summary", f"Scan complete: {len(data)} items")
        elif action == "analyze_project":
            return data.get("summary", f"Analysis complete: {len(data)} items")
        elif action == "trace_code":
            trace = data.get("trace", "")
            if trace:
                return trace[:500] + ("..." if len(trace) > 500 else "")
            return "Trace complete"
        elif action == "get_file":
            file_name = data.get("file", "")
            return f"📄 {file_name} - {data.get('total_lines', 0)} lines"
        elif action == "list_projects":
            return data.get("summary", "Projects listed")
        elif action == "project_summary":
            return data.get("summary", "Project summary")
        elif action == "gallery":
            return data.get("summary", "Gallery displayed")
        elif action == "godmeme_status":
            return data.get("summary", "GodMeme status")
        elif action == "show_log":
            return data.get("summary", "Log displayed")
        elif action == "run_bot":
            return data.get("summary", "Bot running")
        elif action == "modify_logic":
            return data.get("summary", "Logic modified")
        elif action == "repair_project":
            return data.get("summary", "Project repaired")
        elif action == "build_project":
            return data.get("summary", "Project built")
        elif action == "modify_project":
            return data.get("summary", "Project modified")
        elif action == "autonomous_project":
            return data.get("summary", "Autonomous project")
        elif action == "video_info":
            return data.get("summary", "Video info")
        elif action == "business_analysis":
            return data.get("summary", "Business analysis")
        else:
            # Generic
            return "✅ Task selesai" if data.get("success", True) else "❌ Task gagal"
    
    @staticmethod
    def _generate_display(action: str, target: str, data: Dict) -> str:
        """Generate display jika kosong"""
        if action in ["scan_project", "analyze_project"]:
            return f"{action.replace('_', ' ').title()}: {target} selesai"
        elif action == "trace_code":
            return f"Trace {target}: selesai"
        else:
            return f"✅ {action.replace('_', ' ').title()} selesai"
    
    @staticmethod
    def compare(canonical1: Dict, canonical2: Dict) -> Dict:
        """
        Bandingkan dua canonical result.
        
        Returns:
        {
            "match": bool,
            "display_match": bool,
            "success_match": bool,
            "differences": [...]
        }
        """
        # Success harus match
        success_match = canonical1.get("success") == canonical2.get("success")
        
        # Display harus match
        display1 = canonical1.get("display", "")
        display2 = canonical2.get("display", "")
        display_match = display1 == display2
        
        # Summary harus match (jika ada)
        summary1 = canonical1.get("summary", "")
        summary2 = canonical2.get("summary", "")
        summary_match = summary1 == summary2 or not summary1 or not summary2
        
        # Data key harus match (tidak harus value-nya sama)
        data1_keys = set(canonical1.get("data", {}).keys())
        data2_keys = set(canonical2.get("data", {}).keys())
        data_keys_match = data1_keys == data2_keys
        
        # Overall match
        match = success_match and display_match
        
        differences = []
        if not success_match:
            differences.append(f"success: {canonical1.get('success')} vs {canonical2.get('success')}")
        if not display_match:
            differences.append(f"display: {display1[:50]} vs {display2[:50]}")
        if not summary_match:
            differences.append("summary mismatch")
        if not data_keys_match:
            differences.append(f"data keys: {data1_keys} vs {data2_keys}")
        
        return {
            "match": match,
            "display_match": display_match,
            "success_match": success_match,
            "summary_match": summary_match,
            "data_keys_match": data_keys_match,
            "differences": differences
        }


# Singleton
_normalizer = None

def get_normalizer() -> ResultNormalizer:
    global _normalizer
    if _normalizer is None:
        _normalizer = ResultNormalizer()
    return _normalizer
