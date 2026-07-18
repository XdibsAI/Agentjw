"""
Response Composer — Layer untuk menyusun jawaban alami dari hasil planner/executor
"""

from typing import Dict, List, Any, Optional
import json
import re

class ResponseComposer:
    """
    Mengubah hasil planner (JSON) menjadi jawaban alami untuk user
    """
    
    def __init__(self):
        self.severity_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4
        }
    
    def compose(self, planner_result: Dict, context: Dict = None) -> str:
        """
        Mengubah hasil planner menjadi response alami
        """
        # Jika planner_result sudah berupa string, return langsung
        if isinstance(planner_result, str):
            return planner_result
        
        # Jika bukan dict, convert
        if not isinstance(planner_result, dict):
            return str(planner_result)
        
        # Cek apakah ada error
        if planner_result.get("error"):
            return self._handle_error(planner_result["error"])
        
        # Extract components
        intent = planner_result.get("intent", "chat")
        response = planner_result.get("response", "")
        plan = planner_result.get("plan", [])
        action = planner_result.get("action", "null")
        needs_from_user = planner_result.get("needs_from_user", "null")
        reasoning = planner_result.get("reasoning", "")
        
        # Priority issues (jika ada)
        issues = planner_result.get("issues", [])
        
        # Build response
        parts = []
        
        # 1. Main response (dari LLM)
        if response and response != "null":
            parts.append(response)
        
        # 2. Issues dengan prioritas
        if issues:
            parts.append(self._format_issues(issues))
        
        # 3. Plan/actions
        if plan:
            parts.append(self._format_plan(plan))
        
        # 4. Needs from user
        if needs_from_user and needs_from_user != "null":
            parts.append(f"\n📌 {needs_from_user}")
        
        # 5. Follow-up
        if action and action != "null":
            parts.append(f"\n🔄 Saya akan {self._describe_action(action)}")
        
        # Gabungkan
        result = "\n\n".join([p for p in parts if p and p.strip()])
        
        # Jika kosong, fallback
        if not result:
            result = "Saya siap membantu. Ada yang bisa saya bantu?"
        
        return result
    
    def _handle_error(self, error: str) -> str:
        """Handle error dengan cara yang human-friendly"""
        if "API" in error or "timeout" in error.lower():
            return "Maaf, saya sedang mengalami gangguan teknis. Silakan coba lagi nanti."
        return f"Terjadi kesalahan: {error}"
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """Format issues berdasarkan prioritas"""
        if not issues:
            return ""
        
        # Urutkan berdasarkan severity
        sorted_issues = sorted(
            issues, 
            key=lambda x: self.severity_order.get(x.get("severity", "low"), 99)
        )
        
        lines = ["\n📊 **Ringkasan Masalah:**"]
        
        # Kelompokkan berdasarkan severity
        groups = {}
        for issue in sorted_issues:
            severity = issue.get("severity", "low")
            if severity not in groups:
                groups[severity] = []
            groups[severity].append(issue)
        
        # Tampilkan per group
        severity_labels = {
            "critical": "🔴 **Kritis** (Harus segera diperbaiki)",
            "high": "🟠 **Tinggi** (Perlu perhatian)",
            "medium": "🟡 **Sedang**",
            "low": "🟢 **Rendah**",
            "info": "ℹ️ **Informasi**"
        }
        
        for severity, label in severity_labels.items():
            if severity in groups:
                lines.append(f"\n{label}:")
                for issue in groups[severity]:
                    desc = issue.get("description", "")
                    location = issue.get("location", "")
                    if location:
                        lines.append(f"  • {desc} ({location})")
                    else:
                        lines.append(f"  • {desc}")
        
        return "\n".join(lines)
    
    def _format_plan(self, plan: List[Dict]) -> str:
        """Format plan menjadi langkah-langkah"""
        if not plan:
            return ""
        
        lines = ["\n📋 **Rencana Tindakan:**"]
        for i, step in enumerate(plan, 1):
            action = step.get("action", "unknown")
            target = step.get("action_target", "")
            purpose = step.get("purpose", "")
            
            action_desc = self._describe_action(action)
            if target:
                lines.append(f"  {i}. {action_desc} `{target}`")
            else:
                lines.append(f"  {i}. {action_desc}")
            
            if purpose:
                lines.append(f"     _{purpose}_")
        
        return "\n".join(lines)
    
    def _describe_action(self, action: str) -> str:
        """Deskripsikan action dalam bahasa alami"""
        descriptions = {
            "analyze_project": "menganalisis project",
            "list_projects": "menampilkan daftar project",
            "modify_logic": "memperbaiki logic",
            "scan_project": "memindai project",
            "repair_project": "memperbaiki project",
            "build_project": "membangun project",
            "run_bot": "menjalankan bot",
            "show_log": "menampilkan log",
            "godmeme_status": "mengecek status Godmeme",
            "analyze_trading_data": "menganalisis data trading",
            "null": "menunggu instruksi"
        }
        return descriptions.get(action, action.replace("_", " "))
    
    def extract_priority_issues(self, data: Dict) -> List[Dict]:
        """
        Extract priority issues dari data
        """
        issues = []
        
        # Cek broken imports
        if data.get("broken_imports"):
            issues.append({
                "severity": "critical",
                "description": f"{len(data['broken_imports'])} broken import",
                "location": "projects"
            })
        
        # Cek orphan files
        if data.get("orphan_files", 0) > 0:
            issues.append({
                "severity": "medium",
                "description": f"{data['orphan_files']} file orphan",
                "location": "repository"
            })
        
        # Cek duplicate files
        if data.get("duplicate_files", 0) > 0:
            issues.append({
                "severity": "low",
                "description": f"{data['duplicate_files']} file duplikat",
                "location": "repository"
            })
        
        # Cek missing API keys
        if data.get("missing_api_keys"):
            issues.append({
                "severity": "high",
                "description": f"{len(data['missing_api_keys'])} API key belum dikonfigurasi",
                "location": ".env"
            })
        
        return issues

# Singleton
_composer = None

def get_response_composer() -> ResponseComposer:
    global _composer
    if _composer is None:
        _composer = ResponseComposer()
    return _composer
