"""
portfolio/position_manager.py
================================
Mengelola seluruh posisi terbuka: take profit bertingkat, trailing stop,
hard stop loss, time stop, partial sell, PnL tracking (realized +
unrealized). Ini yang dipanggil tiap "tick" oleh main loop untuk semua
posisi terbuka.
"""
from datetime import datetime, timezone
from typing import List, Optional

from config import settings
from core.database import db
from core.logger import get_logger
from core.models import Position, PositionStatus, Trade
from execution.execution_engine import Executor
from risk.risk_manager import RiskManager

log = get_logger("portfolio.position")


class PositionManager:
    def __init__(self, executor: Executor, risk_manager: RiskManager):
        self.executor = executor
        self.risk_manager = risk_manager
        # level TP yang sudah dieksekusi per posisi, supaya tidak jual dobel
        # di level yang sama: {position_id: set(levels_hit)}
        self._tp_hit: dict[int, set] = {}

    def open_position(self, trade: Trade, symbol: str, strategy: str) -> Position:
        pos = Position(
            id=None,
            token_address=trade.token_address,
            symbol=symbol,
            status=PositionStatus.OPEN,
            entry_price_usd=trade.price_usd,
            entry_amount_token=trade.amount_token,
            entry_amount_usd=trade.amount_usd,
            remaining_amount_token=trade.amount_token,
            highest_price_seen=trade.price_usd,
            strategy=strategy,
        )
        pos.id = db.insert_position(pos)
        self._tp_hit[pos.id] = set()
        log.info(f"Posisi dibuka: {symbol} ({trade.token_address[:8]}) "
                 f"@ ${trade.price_usd:.8f} amount=${trade.amount_usd:.2f}")
        return pos

    async def check_all_positions(self) -> None:
        """Dipanggil tiap tick oleh main loop."""
        for row in db.open_positions():
            pos = self._row_to_position(row)
            await self._check_position(pos)

    async def _check_position(self, pos: Position) -> None:
        current_price = await self.executor.get_current_price(pos.token_address)
        if current_price <= 0:
            log.warning(f"Tidak dapat harga untuk {pos.symbol} — skip tick ini")
            return

        if current_price > pos.highest_price_seen:
            pos.highest_price_seen = current_price
            db.update_position(pos)

        pnl_percent = (current_price - pos.entry_price_usd) / pos.entry_price_usd * 100
        drop_from_high = (
            (current_price - pos.highest_price_seen) / pos.highest_price_seen * 100
            if pos.highest_price_seen > 0 else 0
        )
        age_minutes = self._age_minutes(pos.opened_at)

        # ── Hard stop loss ──────────────────────────────────────────
        if pnl_percent <= -settings.hard_stop_loss_percent:
            await self._close_full(pos, current_price, reason=(
                f"Hard stop loss: {pnl_percent:.1f}% <= -{settings.hard_stop_loss_percent}%"
            ))
            return

        # ── Trailing stop (hanya aktif kalau sudah pernah profit) ───
        if pos.highest_price_seen > pos.entry_price_usd:
            if drop_from_high <= -settings.trailing_stop_percent:
                await self._close_full(pos, current_price, reason=(
                    f"Trailing stop: turun {drop_from_high:.1f}% dari puncak "
                    f"${pos.highest_price_seen:.8f}"
                ))
                return

        # ── Time stop ────────────────────────────────────────────────
        if age_minutes >= settings.time_stop_minutes and pnl_percent < 5:
            await self._close_full(pos, current_price, reason=(
                f"Time stop: {age_minutes:.0f} menit tanpa momentum berarti "
                f"(pnl={pnl_percent:.1f}%)"
            ))
            return

        # ── Take profit bertingkat ───────────────────────────────────
        hit_levels = self._tp_hit.setdefault(pos.id, set())
        for level in sorted(settings.take_profit_levels):
            if pnl_percent >= level and level not in hit_levels:
                hit_levels.add(level)
                await self._partial_sell(pos, current_price, fraction=0.33, reason=(
                    f"Take profit level {level}% tercapai (pnl={pnl_percent:.1f}%)"
                ))

    async def _partial_sell(self, pos: Position, price: float, fraction: float, reason: str) -> None:
        amount_to_sell = pos.remaining_amount_token * fraction
        if amount_to_sell <= 0:
            return
        trade = await self.executor.sell(pos.token_address, amount_to_sell, pos.strategy)

        cost_basis = (amount_to_sell / pos.entry_amount_token) * pos.entry_amount_usd
        realized = trade.amount_usd - cost_basis

        pos.remaining_amount_token -= amount_to_sell
        pos.realized_pnl_usd += realized
        db.update_position(pos)

        log.info(f"Partial sell {pos.symbol}: {reason} | realized=${realized:.2f}")

        if pos.remaining_amount_token <= (pos.entry_amount_token * 0.01):
            await self._finalize_close(pos, reason="Semua porsi terjual via take profit bertingkat")

    async def _close_full(self, pos: Position, price: float, reason: str) -> None:
        if pos.remaining_amount_token <= 0:
            await self._finalize_close(pos, reason)
            return
        trade = await self.executor.sell(pos.token_address, pos.remaining_amount_token, pos.strategy)

        cost_basis = (pos.remaining_amount_token / pos.entry_amount_token) * pos.entry_amount_usd
        realized = trade.amount_usd - cost_basis
        pos.realized_pnl_usd += realized
        pos.remaining_amount_token = 0.0
        db.update_position(pos)

        log.info(f"Close full {pos.symbol}: {reason} | realized total=${pos.realized_pnl_usd:.2f}")
        await self._finalize_close(pos, reason)

    async def _finalize_close(self, pos: Position, reason: str) -> None:
        pos.status = PositionStatus.CLOSED
        pos.closed_at = datetime.now(timezone.utc).isoformat()
        pos.exit_reason = reason
        db.update_position(pos)
        self._tp_hit.pop(pos.id, None)

        self.risk_manager.record_trade_outcome(pos.realized_pnl_usd)

        hold_minutes = self._age_minutes(pos.opened_at)
        outcome = "WIN" if pos.realized_pnl_usd > 0 else (
            "LOSS" if pos.realized_pnl_usd < 0 else "BREAKEVEN"
        )
        db.insert_learning_record(
            token_address=pos.token_address,
            strategy=pos.strategy,
            outcome=outcome,
            pnl_usd=pos.realized_pnl_usd,
            hold_minutes=hold_minutes,
            score_at_entry=0.0,  # diisi main.py kalau tersedia dari signal asli
            notes=reason,
            created_at=pos.closed_at,
        )

    @staticmethod
    def _age_minutes(opened_at_iso: str) -> float:
        opened = datetime.fromisoformat(opened_at_iso)
        return (datetime.now(timezone.utc) - opened).total_seconds() / 60.0

    @staticmethod
    def _row_to_position(row: dict) -> Position:
        return Position(
            id=row["id"], token_address=row["token_address"], symbol=row["symbol"],
            status=PositionStatus(row["status"]), entry_price_usd=row["entry_price_usd"],
            entry_amount_token=row["entry_amount_token"], entry_amount_usd=row["entry_amount_usd"],
            remaining_amount_token=row["remaining_amount_token"],
            realized_pnl_usd=row["realized_pnl_usd"], unrealized_pnl_usd=row["unrealized_pnl_usd"],
            highest_price_seen=row["highest_price_seen"], strategy=row["strategy"],
            opened_at=row["opened_at"], closed_at=row["closed_at"], exit_reason=row["exit_reason"],
        )
