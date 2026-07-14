"""
business_analysis - Analisa bisnis dengan Result Contract
"""

from core.llm_client import llm
# # Migrated to adapter  # Migrated to adapter
from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute business_analysis dengan Result Contract"""
    user_request = task.get("user_request", "Analisa bisnis kita")
    
    adapter = get_project_adapter()
    projects = adapter.get_projects()
    if not projects:
        contract = ResultContract(
            success=False,
            action="business_analysis",
            entity="",
            display="❌ Belum ada project untuk dianalisa",
            errors=["Belum ada project untuk dianalisa"]
        )
        return contract.to_dict()
    
    context_lines = []
    for p in projects:
        context_lines.append(
            f"- {p['name']} (tipe: {p['tool_type']}, status: {p['status']}, "
            f"{p['python_files']} file Python, path: {p['project_dir']})"
        )
    
    prompt = (
        "Sebagai SiCuan, analisa bisnis dari SEMUA project berikut (total " + 
        str(len(projects)) + " project):\n\n" +
        "\n".join(context_lines) +
        "\n\nUser bertanya: " + user_request +
        "\n\nWAJIB bahas SEMUA project di atas satu per satu, jangan cuma satu. "
        "Beri rekomendasi konkret: mana yang paling potensial cuan, mana yang harus didrop, "
        "dan urutan prioritas kalau punya waktu/modal terbatas. Jawab natural, actionable, bahasa santai."
    )
    
    try:
        analysis = llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system="Kamu SiCuan, AI partner bisnis yang to-the-point dan strategis. SELALU bahas semua project yang diberikan, jangan skip satupun.",
            temperature=0.6,
            max_tokens=1000
        )
        
        contract = ResultContract(
            success=True,
            action="business_analysis",
            entity="",
            display=analysis,
            metrics={"projects_analyzed": len(projects)},
            confidence=0.8,
            data={"analysis": analysis}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="business_analysis",
            entity="",
            display=f"❌ Gagal melakukan analisa: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
