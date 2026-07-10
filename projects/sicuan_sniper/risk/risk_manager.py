"""
risk/risk_manager.py
======================
Ini modul yang paling penting di seluruh sistem. Tugasnya SATU: mencegah
Signal BUY dieksekusi kalau melanggar batas risiko — apapun skornya.

RiskManager tidak pernah membuat sinyal BUY, hanya menyetujui/menolak.
"""
from datetime import datetime, timedelta, timezone
from typing import Tuple

from config import settings
from core.database import db
from core.logger import get_logger
from core.models import Action, Signal

log = get_logger("risk.manager")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class RiskManager:
    def __init__(self):
        self._last_loss_at: datetime | None = None

    def approve(self, signal: Signal, open_position_count: int) -> Tuple[bool, str]:
        """Return (approved, reason). Semua Signal (bukan cuma BUY) lewat
        sini sebelum dieksekusi — SELL/EMERGENCY_EXIT selalu disetujui
        karena keluar dari posisi tidak pernah menambah risiko baru."""
        if signal.action in (Action.SELL, Action.EMERGENCY_EXIT, Action.SKIP, Action.WATCH):
            return True, "non-BUY signal, selalu diizinkan"

        stats = db.get_daily_stats(today_str())

        if stats["circuit_breaker_tripped"]:
            return False, "Circuit breaker aktif hari ini — trading dihentikan sampai besok"

        if stats["realized_pnl_usd"] <= -abs(settings.max_daily_loss_usd):
            self._trip_circuit_breaker(stats["date"])
            return False, (
                f"Batas rugi harian tercapai (${stats['realized_pnl_usd']:.2f} <= "
                f"-${settings.max_daily_loss_usd}). Circuit breaker diaktifkan."
            )

        loss_percent = (
            abs(stats["realized_pnl_usd"]) / settings.starting_capital_usd * 100
            if stats["realized_pnl_usd"] < 0 else 0
        )
        if loss_percent >= settings.max_daily_loss_percent:
            self._trip_circuit_breaker(stats["date"])
            return False, (
                f"Rugi harian {loss_percent:.1f}% >= batas "
                f"{settings.max_daily_loss_percent}%. Circuit breaker diaktifkan."
            )

        if stats["consecutive_losses"] >= settings.circuit_breaker_consecutive_losses:
            return False, (
                f"{stats['consecutive_losses']} kekalahan beruntun >= batas "
                f"{settings.circuit_breaker_consecutive_losses}. Cooldown wajib."
            )

        if self._last_loss_at is not None:
            cooldown_until = self._last_loss_at + timedelta(minutes=settings.cooldown_after_loss_minutes)
            if datetime.now(timezone.utc) < cooldown_until:
                remaining = (cooldown_until - datetime.now(timezone.utc)).total_seconds() / 60
                return False, f"Dalam cooldown setelah rugi, {remaining:.1f} menit lagi"

        if open_position_count >= settings.max_concurrent_positions:
            return False, (
                f"Slot posisi penuh ({open_position_count}/{settings.max_concurrent_positions})"
            )

        if signal.suggested_size_usd > settings.max_position_size_usd:
            return False, (
                f"Ukuran posisi ${signal.suggested_size_usd:.2f} melebihi batas "
                f"${settings.max_position_size_usd:.2f}"
            )

        return True, "disetujui"

    def record_trade_outcome(self, pnl_usd: float) -> None:
        """Dipanggil setelah posisi ditutup — update daily stats & cek
        apakah perlu trip circuit breaker / mulai cooldown."""
        date = today_str()
        stats = db.get_daily_stats(date)

        new_pnl = stats["realized_pnl_usd"] + pnl_usd
        new_trade_count = stats["trade_count"] + 1
        is_win = pnl_usd > 0
        new_win = stats["win_count"] + (1 if is_win else 0)
        new_loss = stats["loss_count"] + (0 if is_win else 1)
        new_consecutive = 0 if is_win else stats["consecutive_losses"] + 1

        db.update_daily_stats(
            date,
            realized_pnl_usd=new_pnl,
            trade_count=new_trade_count,
            win_count=new_win,
            loss_count=new_loss,
            consecutive_losses=new_consecutive,
        )

        if not is_win:
            self._last_loss_at = datetime.now(timezone.utc)
            log.warning(f"Trade rugi ${pnl_usd:.2f}. Kekalahan beruntun: {new_consecutive}")

        if new_pnl <= -abs(settings.max_daily_loss_usd):
            self._trip_circuit_breaker(date)

    def _trip_circuit_breaker(self, date: str) -> None:
        db.update_daily_stats(date, circuit_breaker_tripped=1)
        log.error(f"🛑 CIRCUIT BREAKER AKTIF untuk {date} — semua BUY baru diblokir hari ini")
