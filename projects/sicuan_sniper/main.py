#!/usr/bin/env python3
"""
main.py
========
Orchestrator utama SiCuan Sniper. Menjalankan:
  DiscoveryEngine -> TokenAnalyzer -> ScoringEngine -> DecisionEngine
      -> RiskManager.approve() -> ExecutionEngine -> PositionManager

PositionManager.check_all_positions() dijalankan tiap tick paralel dengan
discovery loop, supaya posisi terbuka tetap dipantau (TP/SL/trailing)
sementara sistem terus mencari token baru.

Jalankan: python3 main.py
Berhenti : Ctrl+C (aman — tidak ada state yang hilang, semua di SQLite)
"""
import asyncio
import signal

from analyzer.scoring_engine import ScoringEngine
from analyzer.token_analyzer import TokenAnalyzer
from config import settings, require_live_trading_ack
from core.database import db
from core.logger import get_logger
from core.models import Action, Token
from decision.decision_engine import DecisionEngine
from discovery.discovery_engine import DiscoveryEngine
from execution.execution_engine import get_executor
from learning.learning_engine import LearningEngine
from portfolio.position_manager import PositionManager
from reporting.reporting_engine import ReportingEngine
from risk.risk_manager import RiskManager

log = get_logger("main")


class SiCuanSniper:
    def __init__(self):
        require_live_trading_ack()

        self.discovery = DiscoveryEngine(poll_interval_seconds=5.0)
        self.analyzer = TokenAnalyzer()
        self.scoring = ScoringEngine()
        self.decision = DecisionEngine(strategy_name="default")
        self.risk = RiskManager()
        self.executor = get_executor()
        self.positions = PositionManager(self.executor, self.risk)
        self.learning = LearningEngine()
        self.reporting = ReportingEngine()

        self._running = True

    async def handle_new_token(self, token: Token) -> None:
        try:
            analysis = await self.analyzer.analyze(token)
        except Exception as e:
            log.error(f"Analisis gagal untuk {token.symbol} ({token.address[:8]}): {e}")
            return

        score = self.scoring.score(analysis)
        open_count = len(db.open_positions())
        signal = self.decision.decide(token, analysis, score, open_count)

        log.info(f"[{signal.action.value}] {token.symbol} ({token.address[:8]}) "
                  f"score={score.total_score:.1f} — {signal.reason}")

        if signal.action != Action.BUY:
            return

        approved, risk_reason = self.risk.approve(signal, open_count)
        if not approved:
            log.warning(f"BUY ditolak RiskManager untuk {token.symbol}: {risk_reason}")
            return

        try:
            trade = await self.executor.buy(
                token.address, signal.suggested_size_usd, signal.strategy
            )
        except Exception as e:
            log.error(f"Eksekusi BUY gagal untuk {token.symbol}: {e}")
            return

        self.positions.open_position(trade, symbol=token.symbol, strategy=signal.strategy)

    async def position_monitor_loop(self, interval_seconds: float = 3.0):
        while self._running:
            await self.positions.check_all_positions()
            await asyncio.sleep(interval_seconds)

    async def learning_loop(self, interval_seconds: float = 300.0):
        while self._running:
            await asyncio.sleep(interval_seconds)
            self.learning.evaluate_and_adjust()
            self.reporting.print_report()

    async def run(self):
        mode = "PAPER TRADING" if settings.paper_trading else "LIVE TRADING"
        log.info("=" * 60)
        log.info(f"SiCuan Sniper starting — mode: {mode}")
        log.info(f"Modal awal   : ${settings.starting_capital_usd}")
        log.info(f"Max per posisi: ${settings.max_position_size_usd}")
        log.info(f"Max posisi bersamaan: {settings.max_concurrent_positions}")
        log.info(f"Batas rugi harian: ${settings.max_daily_loss_usd} "
                  f"({settings.max_daily_loss_percent}%)")
        log.info("=" * 60)

        if settings.paper_trading:
            log.info("Semua transaksi disimulasikan. Tidak ada dana asli yang dipakai.")

        await asyncio.gather(
            self.discovery.run_forever(self.handle_new_token),
            self.position_monitor_loop(),
            self.learning_loop(),
        )

    def stop(self):
        self._running = False
        log.info("Menghentikan SiCuan Sniper...")


async def _main():
    sniper = SiCuanSniper()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, sniper.stop)
        except NotImplementedError:
            pass  # Windows tidak support add_signal_handler

    try:
        await sniper.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        sniper.reporting.print_report()
        log.info("SiCuan Sniper berhenti. Data tersimpan di SQLite, aman untuk restart.")


if __name__ == "__main__":
    asyncio.run(_main())
