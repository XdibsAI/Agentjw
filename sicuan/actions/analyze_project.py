"""
analyze_project - Analisa project dengan Result Contract + Response Composer
"""

from memory.unified_projects import unified_projects
from sicuan.project_trace import audit_project
from sicuan.core.result_contract import ResultContract
from sicuan.core.response_composer import ResponseComposer
import sqlite3
from pathlib import Path


def execute(task: dict) -> dict:
    """Execute analyze_project dengan Result Contract"""
    target = task.get("target", "")
    projects = unified_projects.list_projects()

    p = None
    for proj in projects:
        if target and target.lower() in proj["name"].lower():
            p = proj
            break

    if not p:
        contract = ResultContract(
            success=False,
            action="analyze_project",
            entity=target,
            display=f"❌ Project '{target}' tidak ditemukan",
            errors=[f"Project '{target}' tidak ditemukan"]
        )
        return contract.to_dict()

    try:
        audit = audit_project(p["project_dir"])
        confidence = audit.get("confidence", 0)
        functions = audit.get("functions", 0)
        
        # === KUMPULKAN FEATURES ===
        features = []
        for key in sorted(audit.get("features", {}).keys()):
            found = audit["features"][key]
            status = "✅" if found else "❌"
            features.append(f"{status} {key}: {'FOUND' if found else 'MISSING'}")

        # === AMBIL DATA TRADING ===
        stats = {}
        recommendations = []
        
        try:
            db_path = Path("projects/godmeme_bot/trading.db")
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
                        SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
                        SUM(realized_pnl) as total_pnl,
                        AVG(realized_pnl) as avg_pnl,
                        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses
                    FROM trades WHERE realized_pnl IS NOT NULL
                """)
                row = cursor.fetchone()
                conn.close()
                
                total = row[0] or 0
                buys = row[1] or 0
                sells = row[2] or 0
                total_pnl = row[3] or 0.0
                avg_pnl = row[4] or 0.0
                wins = row[5] or 0
                losses = row[6] or 0
                winrate = (wins / total * 100) if total > 0 else 0
                
                stats = {
                    "total": total,
                    "buys": buys,
                    "sells": sells,
                    "total_pnl": total_pnl,
                    "avg_pnl": avg_pnl,
                    "wins": wins,
                    "losses": losses,
                    "winrate": winrate
                }
                
                if total > 0:
                    if total_pnl < 0:
                        recommendations.append(f"⚠️ Total PnL negatif: {total_pnl:.4f} SOL")
                    if winrate < 50:
                        recommendations.append(f"⚠️ Win rate rendah: {winrate:.1f}% (target >50%)")
                    if buys == 0 and sells > 0:
                        recommendations.append("⚠️ Bot hanya SELL, tidak ada BUY! Cek score threshold di strategy.py")
                    if losses > wins:
                        recommendations.append(f"⚠️ Loss ({losses}) > Win ({wins})")
                    
                    if total_pnl < 0 and winrate < 50:
                        recommendations.append("🔧 Saran: Turunkan score threshold dari 10 ke 8 di strategy.py")
                    if buys == 0:
                        recommendations.append("🔧 Saran: Periksa kondisi _should_buy di strategy.py")
                else:
                    recommendations.append("ℹ️ Belum ada data trading")
                    
        except Exception as e:
            recommendations.append(f"⚠️ Data trading tidak tersedia: {e}")

        # === GUNAKAN RESPONSE COMPOSER ===
        display = ResponseComposer.compose_analysis(
            project=p['name'],
            stats=stats,
            recommendations=recommendations,
            features=features
        )

        contract = ResultContract(
            success=True,
            action="analyze_project",
            entity=p["name"],
            display=display,
            metrics={
                "confidence": confidence,
                "functions": functions
            },
            confidence=confidence / 100,
            data=audit
        )
        return contract.to_dict()

    except Exception as e:
        contract = ResultContract(
            success=False,
            action="analyze_project",
            entity=p["name"],
            display=f"❌ Error analyzing project: {e}",
            errors=[str(e)]
        )
        return contract.to_dict()
