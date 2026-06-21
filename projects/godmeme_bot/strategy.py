import asyncio
import logging
from status_writer import update_status
import time
from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import os
from pathlib import Path

from config import config
from database import (
    Trade,
    TradeStatus,
    Position as DBPosition,
    PositionStatus
)

logger = logging.getLogger(__name__)

SOL_MINT = "So11111111111111111111111111111111111111112"
PAPER_WALLET_FILE = Path(__file__).parent / "paper_wallet.json"


def load_paper_balance():
    try:
        if PAPER_WALLET_FILE.exists():
            import json
            return float(json.loads(PAPER_WALLET_FILE.read_text()).get("balance", 10.0))
    except Exception:
        pass
    return 10.0


def save_paper_balance(balance):
    try:
        import json
        PAPER_WALLET_FILE.write_text(
            json.dumps({"balance": round(balance, 6)}, indent=2)
        )
    except Exception:
        pass


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

        # Calculate base PNL percentage
        base_pnl = ((current_price - self.entry_price) / self.entry_price) * 100

        # Enhanced volatility factor with exponential scaling
        volatility_factor = min(max(abs(base_pnl) / 50, 0.2), 1.5)

        # Dynamic position sizing based on account risk exposure
        position_factor = min(self.position_size / 500, 1.0) if hasattr(self, 'position_size') else 1.0

        # Add profit-taking acceleration factor
        profit_accelerator = 1.0 + min(max(base_pnl, 0) / 200, 0.5)

        # Calculate risk-adjusted return with enhanced factors
        risk_adjusted_pnl = base_pnl * volatility_factor * position_factor * profit_accelerator

        return risk_adjusted_pnl


class Strategy:

    async def get_token_price_paper(self, mint: str):
        try:
            import aiohttp

            url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    data = await r.json()

            pairs = data.get("pairs") or []

            if not pairs:
                return None

            pair = max(
                pairs,
                key=lambda x: float(
                    x.get("liquidity", {}).get("usd", 0) or 0
                )
            )

            price = pair.get("priceUsd")

            if not price:
                return None

            return float(price)

        except Exception as e:
            logger.warning(f"price lookup failed {mint[:8]}: {e}")
            return None

    def __init__(self, wallet, jupiter, raydium_client=None, db=None, notifier=None):
        self.wallet = wallet
        self.jupiter = jupiter
        self.raydium = raydium_client
        self.db = db
        self.notifier = notifier
        self.positions: Dict[str, Position] = {}
        self.daily_pnl_sol = 0.0

        # Persistent paper wallet balance
        self.paper_balance = load_paper_balance()

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
                async with aiohttp.ClientSession() as session:

                    # NEW TOKEN DISCOVERY
                    async with session.get(
                        "https://api.dexscreener.com/token-profiles/latest/v1",
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as r:

                        if r.status != 200:
                            logger.warning(f"token-profiles status={r.status}")
                            return []

                        profiles = await r.json()

                    logger.debug(f"Retrieved {len(profiles)} token profiles")

                    for profile in profiles[:50]:

                        if profile.get("chainId") != "solana":
                            continue

                        mint = profile.get("tokenAddress")
                        if not mint:
                            continue

                        try:
                            async with session.get(
                                f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
                                timeout=aiohttp.ClientTimeout(total=15)
                            ) as pr:

                                if pr.status != 200:
                                    continue

                                pdata = await pr.json()

                            pairs = pdata.get("pairs", [])
                            if not pairs:
                                continue

                            pair = max(
                                pairs,
                                key=lambda x: float(
                                    x.get("liquidity", {}).get("usd", 0) or 0
                                )
                            )

                            liq = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                            vol5m = float(pair.get("volume", {}).get("m5", 0) or 0)
                            mcap = float(pair.get("marketCap", 0) or 0)

                            created = pair.get("pairCreatedAt")
                            if created:
                                age_min = (time.time() - created / 1000) / 60
                            else:
                                age_min = 999999

                            if (
                                liq >= config.MIN_LIQUIDITY_USD
                                and mcap <= config.MAX_MCAP_USD
                            ):

                                token_data = {
                                    "mint": mint,
                                    "symbol": pair.get("baseToken", {}).get("symbol", "?"),
                                    "price": float(pair.get("priceUsd", 0) or 0),
                                    "liquidity": liq,
                                    "volume5m": vol5m,
                                    "mcap": mcap,
                                    "age_min": age_min,
                                    "price_change5m": float(
                                        pair.get("priceChange", {}).get("m5", 0) or 0
                                    ),
                                    "dex": pair.get("dexId", ""),
                                }

                                logger.debug(f"Found token: {token_data['symbol']} ({mint[:8]}) - "
                                           f"liquidity=${liq:,.2f}, mcap=${mcap:,.2f}")

                                tokens.append(token_data)

                        except Exception as e:
                            logger.warning(f"token {mint[:8]} scan error: {e}")

            except Exception as e:
                logger.error(f"DexScreener scan error: {e}")

            logger.info(f"Discovered {len(tokens)} tokens")
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

        if price_change < 10:
            return False

        # Brain learned: avoid chasing tokens that already pumped too far
        if price_change >= 50:
            logger.info(
                f"SKIP {token['symbol']} already pumped +{price_change:.1f}%"
            )
            return False
        volume = token.get("volume5m", 0)
        liquidity = token.get("liquidity", 0)
        mcap = token.get("mcap", 0)
        age = token.get("age_min", 999)

        if age > 360:
            return False

        # Brain learned:
        # Hindari entry lemah dan token yang sudah terlalu pump.
        # Fokus early momentum dengan liquidity sehat.

        if price_change < 10:
            logger.info(
                f"SKIP {token['symbol']} weak momentum +{price_change:.1f}%"
            )
            return False

        if price_change >= 35:
            logger.info(
                f"SKIP {token['symbol']} late entry +{price_change:.1f}%"
            )
            return False

        if liquidity < 20000:
            logger.info(
                f"SKIP {token['symbol']} low liquidity ${liquidity:,.0f}"
            )
            return False

        score = 0

        if price_change >= 10:
            score += 2

        if volume >= config.MIN_VOLUME_5M_USD:
            score += 2

        if liquidity >= config.MIN_LIQUIDITY_USD:
            score += 2

        if 3 <= age <= 60:
            score += 1

        if 25000 <= mcap <= config.MAX_MCAP_USD:
            score += 2

        if price_change >= 25:
            score += 1

        print(
            "SCORE",
            token.get("symbol"),
            "score=", score,
            "age=", age,
            "vol=", volume,
            "liq=", liquidity,
            "mcap=", mcap,
            "chg=", price_change
        )

        # Brain learned:
        # Score 6 terlalu longgar dan menghasilkan banyak stop loss.
        # Prioritaskan entry score >= 8.
        should = score >= 9

        if should:
            logger.info(f"BUY signal: {token['symbol']} | score={score} | liq=${liquidity:,.0f} | vol5m=${volume:,.0f} | +{price_change:.1f}%")
        else:
            logger.info(
                f"SKIP {token['symbol']} score too low: {score}"
            )

        return should

    async def _open_position(self, token: Dict):
        mint = token["mint"]
        symbol = token["symbol"]
        sol_amount = config.DEFAULT_POSITION_SIZE_SOL
        entry_price = token.get("price", 0)

        logger.info(f"Opening position: {symbol} | {sol_amount} SOL | ${entry_price:.8f}")

        if config.PAPER_TRADING:
            import uuid
            tx_hash = "PAPER_" + str(uuid.uuid4())[:8]
            logger.info(f"[PAPER] BUY simulated: {tx_hash}")
            update_status(last_event=f"PAPER BUY {token['symbol']}")
        else:
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

        if config.PAPER_TRADING:
            self.paper_balance -= sol_amount
            save_paper_balance(self.paper_balance)

            logger.info(
                f"PAPER BUY BALANCE | "
                f"-{sol_amount:.4f} SOL | "
                f"balance={self.paper_balance:.4f}"
            )

            update_status(
                last_event=f"PAPER BUY {symbol}",
                balance=round(self.paper_balance, 4),
            )

        if self.db:
            try:
                db_pos = DBPosition(
                    id=None,
                    token_address=mint,
                    token_symbol=symbol,
                    side="LONG",
                    amount=Decimal(str(sol_amount)),
                    entry_price=Decimal(str(entry_price)),
                    status=PositionStatus.OPEN,
                    created_at=time.time(),
                    updated_at=time.time(),
                    strategy="godmeme_score",
                    stop_loss=Decimal(str(sl_price)),
                    take_profit=Decimal(str(tp_price)),
                    realized_pnl=None
                )

                self.db.save_position(db_pos)
                logger.info(f"DB POSITION saved: {symbol}")

            except Exception as e:
                logger.error(f"DB POSITION save failed: {e}")

        if self.db:
            try:
                trade = Trade(
                    id=None,
                    token_address=mint,
                    token_symbol=symbol,
                    side="BUY",
                    amount=str(sol_amount),
                    price=str(entry_price),
                    slippage="0",
                    status=TradeStatus.FILLED,
                    tx_hash=tx_hash,
                    created_at=time.time(),
                    updated_at=time.time(),
                    strategy="godmeme_score",
                    fees="0",
                    realized_pnl=None
                )

                self.db.save_trade(trade)
                logger.info(f"DB BUY saved: {symbol}")

                update_status(
                    last_event=f"PAPER BUY {symbol}",
                    trades_today=self.trade_count,
                    open_positions=[
                        {
                            "symbol": p.token_symbol,
                            "entry": p.entry_price,
                            "sol": p.entry_sol,
                            "sl": p.stop_loss_price,
                            "tp": p.take_profit_price
                        }
                        for p in self.positions.values()
                    ]
                )

            except Exception as e:
                logger.error(f"DB BUY failed: {e}")

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
                    if config.PAPER_TRADING:
                        current_price = await self.get_token_price_paper(mint)
                    else:
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
                    elif held_min >= 120:
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
        if config.PAPER_TRADING:
            import uuid
            tx_hash = "PAPER_SELL_" + str(uuid.uuid4())[:8]
        else:
            tx_hash = await self.jupiter.execute_sell(
                mint,
                token_amount_int,
                self.wallet
            )

        pnl_sol = pos.entry_sol * (current_price - pos.entry_price) / pos.entry_price
        self.daily_pnl_sol += pnl_sol

        if config.PAPER_TRADING:
            self.paper_balance += (pos.entry_sol + pnl_sol)
            save_paper_balance(self.paper_balance)

            logger.info(
                f"PAPER SELL BALANCE | "
                f"+{pos.entry_sol + pnl_sol:.4f} SOL | "
                f"balance={self.paper_balance:.4f}"
            )

        if self.db:
            try:
                trade = Trade(
                    id=None,
                    token_address=mint,
                    token_symbol=pos.token_symbol,
                    side="SELL",
                    amount=str(pos.entry_sol),
                    price=str(current_price),
                    slippage="0",
                    status=TradeStatus.FILLED,
                    tx_hash=tx_hash,
                    created_at=time.time(),
                    updated_at=time.time(),
                    strategy="godmeme_score",
                    fees="0",
                    realized_pnl=str(pnl_sol)
                )

                self.db.save_trade(trade)
                logger.info(f"DB SELL saved: {pos.token_symbol}")

                try:
                    positions = self.db.get_positions_by_token(mint)

                    for db_pos in positions:
                        db_pos.status = PositionStatus.CLOSED
                        db_pos.realized_pnl = Decimal(str(pnl_sol))
                        db_pos.updated_at = time.time()
                        self.db.save_position(db_pos)

                    logger.info(f"DB POSITION CLOSED: {pos.token_symbol}")

                except Exception as e:
                    logger.error(f"DB POSITION CLOSE failed: {e}")

            except Exception as e:
                logger.error(f"DB SELL failed: {e}")
        del self.positions[mint]

        update_status(
            last_event=f"PAPER SELL {pos.token_symbol} pnl {pnl_sol:+.4f} SOL",
            daily_pnl=round(self.daily_pnl_sol, 4),
            trades_today=self.trade_count,
            open_positions=[
                {
                    "symbol": p.token_symbol,
                    "entry": p.entry_price,
                    "sol": p.entry_sol,
                    "sl": p.stop_loss_price,
                    "tp": p.take_profit_price
                }
                for p in self.positions.values()
            ]
        )

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
# TODO AUTO OPTIMIZATION: holder_concentration

# TODO AUTO OPTIMIZATION: mint_authority_check

# TODO AUTO OPTIMIZATION: freeze_authority_check