"""
gallery - Gallery media dengan Result Contract
"""

from memory.media_registry import gallery_summary, scan_and_index
from sicuan.core.result_contract import ResultContract


def execute(task: dict) -> dict:
    """Execute gallery dengan Result Contract"""
    try:
        scan_and_index()
        summary = gallery_summary()
        
        # Hitung items dari summary
        items = 0
        import re
        match = re.search(r'\((\d+)\s*item', summary)
        if match:
            items = int(match.group(1))
        
        contract = ResultContract(
            success=True,
            action="gallery",
            entity="",
            display=summary,
            metrics={"items": items},
            confidence=1.0,
            data={"summary": summary}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="gallery",
            entity="",
            display=f"❌ Gagal menampilkan gallery: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
