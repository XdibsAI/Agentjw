"""
Legacy Adapter - Konversi output legacy ke Result Contract
"""

from sicuan.core.result_contract import ResultContract
from core.logger import logger


class LegacyAdapter:
    """Adapter untuk mengkonversi output legacy ke Result Contract"""
    
    @staticmethod
    def adapt(action: str, target: str, legacy_output: str, duration: float = 0) -> ResultContract:
        """
        Konversi output legacy ke Result Contract.
        
        Args:
            action: Nama action
            target: Target action
            legacy_output: Output dari legacy (string)
            duration: Durasi eksekusi
        
        Returns:
            ResultContract
        """
        if not legacy_output:
            return ResultContract(
                success=False,
                action=action,
                entity=target or "",
                display="❌ Legacy output kosong",
                errors=["Legacy output kosong"]
            )
        
        # Deteksi success dari output
        success = LegacyAdapter._is_success(legacy_output)
        
        # Extract entity
        entity = LegacyAdapter._extract_entity(action, target, legacy_output)
        
        # Extract metrics
        metrics = LegacyAdapter._extract_metrics(action, legacy_output)
        
        # Confidence
        confidence = 0.9 if success else 0.2
        
        return ResultContract(
            success=success,
            action=action,
            entity=entity,
            display=legacy_output[:1000],
            metrics=metrics,
            confidence=confidence,
            duration=duration,
            data={"raw": legacy_output}
        )
    
    @staticmethod
    def _is_success(output: str) -> bool:
        """Deteksi apakah output menunjukkan success"""
        success_keywords = [
            "✅", "sukses", "berhasil", "selesai", "complete", "success",
            "valid", "files valid", "functions", "confidence"
        ]
        failure_keywords = [
            "❌", "gagal", "error", "failed", "tidak ditemukan", "not found",
            "exception", "timeout", "invalid"
        ]
        
        output_lower = output.lower()
        
        # Cek failure dulu
        for kw in failure_keywords:
            if kw in output_lower:
                return False
        
        # Cek success
        for kw in success_keywords:
            if kw in output_lower:
                return True
        
        # Default: jika ada output dan tidak ada failure keyword
        return len(output) > 10
    
    @staticmethod
    def _extract_entity(action: str, target: str, output: str) -> str:
        """Extract entity dari output"""
        if target:
            return target
        
        # Coba extract dari output
        import re
        patterns = {
            "scan_project": r"Scan ([a-zA-Z0-9_]+):",
            "analyze_project": r"Project ([a-zA-Z0-9_]+):",
            "repair_project": r"Repair ([a-zA-Z0-9_]+)",
            "build_project": r"Project '([^']+)'",
            "modify_project": r"Project '([^']+)'",
        }
        
        pattern = patterns.get(action)
        if pattern:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return ""
    
    @staticmethod
    def _extract_metrics(action: str, output: str) -> dict:
        """Extract metrics dari output"""
        metrics = {}
        import re
        
        if action == "scan_project":
            match = re.search(r'(\d+)/(\d+) files valid', output)
            if match:
                metrics["valid_files"] = int(match.group(1))
                metrics["total_files"] = int(match.group(2))
        
        elif action == "analyze_project":
            match = re.search(r'confidence (\d+\.?\d*)%', output)
            if match:
                metrics["confidence"] = float(match.group(1))
            match = re.search(r'(\d+) functions', output)
            if match:
                metrics["functions"] = int(match.group(1))
        
        elif action == "repair_project":
            match = re.search(r'(\d+)/(\d+) files valid', output)
            if match:
                metrics["valid_files"] = int(match.group(1))
                metrics["total_files"] = int(match.group(2))
        
        return metrics


def adapt_legacy(action: str, target: str, legacy_output: str, duration: float = 0) -> ResultContract:
    """Konversi output legacy ke Result Contract"""
    return LegacyAdapter.adapt(action, target, legacy_output, duration)
