"""
godmeme_status - Status trading bot dengan Result Contract
"""

from projects.godmeme_bot.status_sync_provider import get_godmeme_status
from sicuan.core.result_contract import ResultContract


def execute(task: dict) -> dict:
    """Execute godmeme_status dengan Result Contract"""
    try:
        data = get_godmeme_status()
        
        process = data.get("process", {})
        database = data.get("database", {})
        positions = data.get("positions", [])
        
        # Build display
        lines = []
        lines.append("🤖 GODMEME BOT STATUS")
        lines.append("=" * 40)
        lines.append("")
        
        proc_status = process.get("status", "unknown")
        proc_icon = "🟢" if proc_status == "running" else "🔴" if proc_status == "stopped" else "🟡"
        lines.append(f"{proc_icon} Process: {proc_status}")
        if process.get("pid"):
            lines.append(f"   PID: {process.get('pid')}")
        if process.get("uptime"):
            lines.append(f"   Uptime: {process.get('uptime')}")
        lines.append("")
        
        db_status = database.get("status", "unknown")
        db_icon = "🟢" if db_status == "ok" else "🔴"
        lines.append(f"{db_icon} Database: {db_status}")
        if database.get("records"):
            lines.append(f"   Records: {database.get('records')}")
        lines.append("")
        
        if positions:
            lines.append(f"📊 Open Positions: {len(positions)}")
            for p in positions[:5]:
                symbol = p.get('symbol', '-')
                amount = p.get('amount', 0)
                pnl = p.get('pnl', 0)
                pnl_icon = "📈" if pnl > 0 else "📉" if pnl < 0 else "⚪"
                lines.append(f"  {pnl_icon} {symbol}: {amount} SOL (PnL: {pnl:.4f} SOL)")
        else:
            lines.append("📊 Open Positions: 0")
        
        lines.append("")
        lines.append("=" * 40)
        
        total_pnl = data.get("total_pnl", 0)
        if total_pnl:
            pnl_icon = "📈" if total_pnl > 0 else "📉" if total_pnl < 0 else "⚪"
            lines.append(f"{pnl_icon} Total PnL: {total_pnl:.4f} SOL")
        
        display = "\n".join(lines)
        
        contract = ResultContract(
            success=True,
            action="godmeme_status",
            entity="godmeme_bot",
            display=display,
            metrics={
                "status": proc_status,
                "positions": len(positions),
                "total_pnl": total_pnl
            },
            confidence=0.95,
            data=data
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="godmeme_status",
            entity="godmeme_bot",
            display=f"❌ Gagal mendapatkan status GodMeme: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
