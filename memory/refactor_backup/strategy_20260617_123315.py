import asyncio
import logging
import time
from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import os

from config import config

logger = logging.getLogger(__name__)

SOL_MINT = "So11111111111111111111111111111111111111112"

@dataclass
class Position:
    token_mint: str
    token_symbol: str
    entry_price: float
    entry_sol: float
    token_amount: float
    entry_time: float = field(default_factory=time.time)
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    tx_hash: str = ""

    def pnl_percent(self, current_price: float) -> float:
        if self.entry_price <= 0:
            return 0.0
        return ((current_price - self.entry_price) / self.entry_price) * 100

class Strategy:
    def __init__(self, wallet, jupiter, raydium_client=None, db=None, notifier=None):
        self.wallet = wallet
        self.jupiter = jupiter
        self.raydium = raydium_client
        self.db = db
        self.notifier = notifier
        self.positions: Dict[str, Position] = {}
        self.daily_pnl_sol = 0.0
        self.trade_count = 0
        self.running = False
        self.logger = logger

    async def run(self):
        self.running = True
        logger.info(f"Strategy started | Paper: {config.PAPER_TRADING} | RPC: {config.get_rpc()[:40]}")
        await asyncio.gather(
            self._monitor_new_tokens(),
            self._monitor_positions(),
        )

    async def _monitor_new_tokens(self):
        logger.info("Token monitor started - scanning DexScreener + Pump.fun")
        while self.running:
            try:
                tokens = await self._scan_new_tokens()
                for token in tokens:
                    if await self._should_buy(token):
                        await self._open_position(token)
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Token monitor error: {e}")
                await asyncio.sleep(15)

    async def _scan_new_tokens(self) -> List[Dict]:
        tokens = []
        try:
            # DexScreener - new Solana pairs
            async with aiohttp.ClientSession() as session:
                url = "https://api.dexscreener.com/latest/dex/search?q=solana"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json()
                        pairs = data.get("pairs", [])
                        for pair in pairs[:20]:
                            if pair.get("chainId") != "solana":
                                continue
                            liq = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                            vol5m = float(pair.get("volume", {}).get("m5", 0) or 0)
                            mcap = float(pair.get("marketCap", 0) or 0)
                            age_min = (time.time() - pair.get("pairCreatedAt", time.time()*1000)/1000) / 60

                            if (liq >= config.MIN_LIQUIDITY_USD and
                                vol5m >= config.MIN_VOLUME_5M_USD and
                                mcap <= config.MAX_MCAP_USD and
                                age_min <= 60):
                                tokens.append({
                                    "mint": pair.get("baseToken", {}).get("address", ""),
                                    "symbol": pair.get("baseToken", {}).get("symbol", "?"),
                                    "price": float(pair.get("priceUsd", 0) or 0),
                                    "liquidity": liq,
                                    "volume5m": vol5m,
                                    "mcap": mcap,
                                    "age_min": age_min,
                                    "price_change5m": float(pair.get("priceChange", {}).get("m5", 0) or 0),
                                    "dex": pair.get("dexId", ""),
                                })
        except Exception as e:
            logger.error(f"DexScreener scan error: {e}")
        return tokens

    async def _should_buy(self, token: Dict) -> bool:
        mint = token.get("mint", "")
        if not mint or len(mint) < 30:
            return False
        if mint in self.positions:
            return False
        if len(self.positions) >= config.MAX_OPEN_POSITIONS:
            return False
        if self.daily_pnl_sol <= -config.MAX_DAILY_LOSS_SOL:
            logger.warning(f"Daily loss limit reached: {self.daily_pnl_sol:.4f} SOL")
            return False
        bal = await self.wallet.get_balance()
        if bal < config.DEFAULT_POSITION_SIZE_SOL * 1.1:
            logger.warning(f"Insufficient balance: {bal:.4f} SOL")
            return False

        # Entry criteria
        price_change = token.get("price_change5m", 0)
        volume = token.get("volume5m", 0)
        liquidity = token.get("liquidity", 0)
        age = token.get("age_min", 999)

        score = 0
        if price_change > 5: score += 2
        if price_change > 15: score += 1
        if volume > 10000: score += 2
        if liquidity > 50000: score += 1
        if age < 10: score += 2  # Fresh token bonus
        if age < 30: score += 1

        should = score >= 4
        if should:
            logger.info(f"BUY signal: {token['symbol']} | score={score} | liq=${liquidity:,.0f} | vol5m=${volume:,.0f} | +{price_change:.1f}%")
        return should

    async def _open_position(self, token: Dict):
        mint = token["mint"]
        symbol = token["symbol"]
        sol_amount = config.DEFAULT_POSITION_SIZE_SOL
        entry_price = token.get("price", 0)

        logger.info(f"Opening position: {symbol} | {sol_amount} SOL | ${entry_price:.8f}")

        tx_hash = await self.jupiter.execute_buy(mint, sol_amount, self.wallet)
        if not tx_hash:
            logger.error(f"Buy failed for {symbol}")
            return

        sl_price = entry_price * (1 - config.STOP_LOSS_PERCENT / 100)
        tp_price = entry_price * config.TAKE_PROFIT_MULTIPLIER

        pos = Position(
            token_mint=mint,
            token_symbol=symbol,
            entry_price=entry_price,
            entry_sol=sol_amount,
            token_amount=sol_amount / entry_price if entry_price > 0 else 0,
            stop_loss_price=sl_price,
            take_profit_price=tp_price,
            tx_hash=tx_hash,
        )
        self.positions[mint] = pos
        self.trade_count += 1

        msg = (
            f"{'📄 PAPER' if config.PAPER_TRADING else '🟢'} BUY {symbol}\n"
            f"Amount: {sol_amount} SOL\n"
            f"Entry: ${entry_price:.8f}\n"
            f"SL: ${sl_price:.8f} (-{config.STOP_LOSS_PERCENT}%)\n"
            f"TP: ${tp_price:.8f} (x{config.TAKE_PROFIT_MULTIPLIER})\n"
            f"TX: {tx_hash[:16]}..."
        )
        logger.info(msg)
        if self.notifier:
            await self.notifier.send(msg)

    async def _monitor_positions(self):
        logger.info("Position monitor started")
        while self.running:
            try:
                for mint, pos in list(self.positions.items()):
                    current_price = await self.jupiter.get_token_price(mint)
                    if not current_price or current_price <= 0:
                        continue

                    pnl = pos.pnl_percent(current_price)
                    held_min = (time.time() - pos.entry_time) / 60

                    should_sell = False
                    reason = ""

                    if current_price <= pos.stop_loss_price:
                        should_sell = True
                        reason = f"Stop Loss {pnl:.1f}%"
                    elif current_price >= pos.take_profit_price:
                        should_sell = True
                        reason = f"Take Profit +{pnl:.1f}%"
                    elif held_min >= 240:
                        should_sell = True
                        reason = f"Time Stop (4h) {pnl:.1f}%"

                    if should_sell:
                        await self._close_position(mint, pos, current_price, reason)

                await asyncio.sleep(15)
            except Exception as e:
                logger.error(f"Position monitor error: {e}")
                await asyncio.sleep(20)

    async def _close_position(self, mint: str, pos: Position, current_price: float, reason: str):
        logger.info(f"Closing {pos.token_symbol} | {reason}")
        token_amount_int = int(pos.token_amount * 1e6)
        tx_hash = await self.jupiter.execute_sell(mint, token_amount_int, self.wallet)

        pnl_sol = pos.entry_sol * (current_price - pos.entry_price) / pos.entry_price
        self.daily_pnl_sol += pnl_sol
        del self.positions[mint]

        pnl_pct = pos.pnl_percent(current_price)
        icon = "🟢" if pnl_sol > 0 else "🔴"
        msg = (
            f"{'📄 PAPER' if config.PAPER_TRADING else icon} SELL {pos.token_symbol}\n"
            f"Reason: {reason}\n"
            f"PnL: {pnl_sol:+.4f} SOL ({pnl_pct:+.1f}%)\n"
            f"Daily PnL: {self.daily_pnl_sol:+.4f} SOL\n"
            f"TX: {(tx_hash or 'failed')[:16]}..."
        )
        logger.info(msg)
        if self.notifier:
            await self.notifier.send(msg)

    def get_status(self) -> Dict:
        return {
            "running": self.running,
            "paper_trading": config.PAPER_TRADING,
            "open_positions": len(self.positions),
            "daily_pnl_sol": round(self.daily_pnl_sol, 4),
            "trade_count": self.trade_count,
            "rpc": config.get_rpc()[:40],
            "positions": [
                {"symbol": p.token_symbol, "entry": p.entry_price, "sol": p.entry_sol}
                for p in self.positions.values()
            ]
        }

    def stop(self):
        self.running = False