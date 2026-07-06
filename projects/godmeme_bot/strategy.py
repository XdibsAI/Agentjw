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

        return (
            (current_price - self.entry_price)
            / self.entry_price
        ) * 100


class Strategy:

    async def _is_blacklisted(self, token_symbol: str) -> bool:
        """Cek apakah token di blacklist"""
        return token_symbol in self.TOKEN_BLACKLIST

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
        
        # Token blacklist - berdasarkan data entry quality
        self.TOKEN_BLACKLIST = [
            "DAWN",      # 0% win rate from 9 trades
            "gary",      # 0% win rate from 5 trades
            "PIXEL",     # 0% win rate from 5 trades
            "くまきち",   # 0% win rate from 5 trades
            "VOYAGER",   # 16.7% win rate - marginal
        ]

        # Persistent paper wallet balance
        self.paper_balance = load_paper_balance()

        self.trade_count = 0
        self.running = False
        self.logger = logger

    async def _restore_open_positions(self):
        try:
            if not self.db:
                return

            positions = self.db.get_open_positions()

            restored = 0

            for p in positions:

                if not p.token_amount:
                    continue

                pos = Position(
                    token_mint=p.token_address,
                    token_symbol=p.token_symbol,
                    entry_price=float(p.entry_price),
                    entry_sol=float(p.entry_sol or 0),
                    token_amount=float(p.token_amount),
                    stop_loss_price=float(p.stop_loss or 0),
                    take_profit_price=float(p.take_profit or 0),
                    tx_hash=p.tx_hash or ""
                )

                self.positions[p.token_address] = pos
                restored += 1

            logger.info(f"RESTORED {restored} OPEN POSITIONS")

        except Exception as e:
            logger.error(f"restore failed: {e}")



    async def run(self):
        self.running = True
        await self._restore_open_positions()
        logger.info(f"Strategy started | Paper: {config.PAPER_TRADING} | RPC: {config.get_rpc()[:40]}")
        await asyncio.gather(
            self._monitor_new_tokens(),
            self._monitor_positions(),
        )

    async def _monitor_new_tokens(self):
        logger.info("Token monitor started - scanning DexScreener + Pump.fun")
        while self.running:
            try:
                # Check cooldown mode (daily loss protection)
                if await self._check_cooldown():
                    await asyncio.sleep(30)  # Check again in 30s
                    continue
                
                tokens = await self._scan_new_tokens()
                for token in tokens:
                    if await self._should_buy(token):
                        # Check risk management before opening position
                        if await self.risk_manager.can_open_position():
                            await self._open_position(token)
                        else:
                            logger.warning("Risk manager blocked new position - max positions reached or insufficient balance")
                    # Add monitoring for existing positions
                    await self._monitor_positions()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Token monitor error: {e}")
                # Check if it's 429 (rate limit)
                if "429" in str(e) or "rate limit" in str(e).lower():
                    await self._handle_429()
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


    async def _should_buy(self, token: Dict, market_condition=None) -> bool:
        # === BLACKLIST CHECK ===
        symbol = token.get("symbol", "")
        if await self._is_blacklisted(symbol):
            logger.info(f"SKIP {symbol} - blacklisted (low win rate)")
            return False
        
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

        # Brain learned: stricter momentum filter to avoid weak pumps
        if price_change < 12:
            return False

        # Brain learned: avoid chasing tokens that already pumped too far
        if price_change >= 45:
            logger.info(
                f"SKIP {token['symbol']} already pumped +{price_change:.1f}%"
            )
            return False
        volume = token.get("volume5m", 0)
        liquidity = token.get("liquidity", 0)
        mcap = token.get("mcap", 0)
        age = token.get("age_min", 999)

        # Brain learned: tighter age filter for higher quality tokens
        if age < 5:
            return False

        if age > 45:
            return False

        # Brain learned:
        # Hindari entry lemah dan token yang sudah terlalu pump.
        # Fokus early momentum dengan liquidity sehat.

        if price_change < 12:
            logger.info(
                f"SKIP {token['symbol']} weak momentum +{price_change:.1f}%"
            )
            return False

        # Brain learned: earlier cutoff for late entries
        if price_change >= 30:
            logger.info(
                f"SKIP {token['symbol']} late entry +{price_change:.1f}%"
            )
            return False

        # Brain learned: higher liquidity requirement
        if liquidity < 35000:
            logger.info(
                f"SKIP {token['symbol']} low liquidity ${liquidity:,.0f}"
            )
            return False

        if volume < liquidity * 0.5:
            logger.info(
                f"SKIP {token['symbol']} weak vol/liquidity ratio "
                f"vol=${volume:,.0f} liq=${liquidity:,.0f}"
            )
            return False

        score = 0

        # Brain learned: weight price change more heavily
        if price_change >= 15:
            score += 3
        if price_change >= 25:
            score += 2

        if volume >= config.MIN_VOLUME_5M_USD * 1.5:
            score += 2

        if liquidity >= config.MIN_LIQUIDITY_USD * 1.2:
            score += 3

        # Brain learned: tighter age window for optimal entries
        if 5 <= age <= 45:
            score += 2

        # Brain learned: tighter market cap filter for quality tokens
        if 50000 <= mcap <= config.MAX_MCAP_USD * 0.8:
            score += 2

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
        # Score 10 is too strict, Score 6 is too loose.
        # Optimal score threshold is 8 for better quality filters.
        should = score >= 8

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
                    current_price = await self.get_token_price_paper(mint)

                    if not current_price or current_price <= 0:
                        continue

                    # Price anomaly check - reject extreme price movements
                    if pos.entry_price > 0:
                        price_change_pct = abs((current_price - pos.entry_price) / pos.entry_price) * 100
                        if price_change_pct > 500:  # More than 500% change likely indicates price anomaly
                            logger.warning(f"Price anomaly detected for {mint}: {price_change_pct:.2f}% change")
                            continue

                    pnl = pos.pnl_percent(current_price)
                    held_min = (time.time() - pos.entry_time) / 60

                    should_sell = False
                    reason = ""

                    # Use USD-based calculations for consistency
                    current_value_usd = current_price * float(pos.token_amount)
                    entry_value_usd = pos.entry_price * float(pos.token_amount)

                    # Dynamic stop loss based on volatility and market conditions
                    volatility_adjusted_stop_loss = config.STOP_LOSS_PERCENT * (1 + pos.volatility)

                    # Enhanced trailing stop with volatility adjustment
                    if not hasattr(pos, 'highest_price'):
                        pos.highest_price = pos.entry_price

                    if current_price > pos.highest_price:
                        pos.highest_price = current_price

                    # Debug logging for position monitoring
                    logger.debug(f"Monitoring position {mint}: price={current_price}, entry={pos.entry_price}, pnl={pnl:.2f}%, held_min={held_min:.1f}")

                    # Multi-tier exit strategy
                    # Tier 1: Immediate stop loss
                    if entry_value_usd > 0 and current_value_usd <= (
                        entry_value_usd * (1 - volatility_adjusted_stop_loss / 100)
                    ):
                        should_sell = True
                        reason = f"Stop Loss {pnl:.1f}%"
                        logger.debug(f"Stop loss triggered for {mint}: {reason}")

                    # Tier 2: Take profit with dynamic scaling
                    elif entry_value_usd > 0 and current_value_usd >= (
                        entry_value_usd * config.TAKE_PROFIT_MULTIPLIER
                    ):
                        should_sell = True
                        reason = f"Take Profit +{pnl:.1f}%"
                        logger.debug(f"Take profit triggered for {mint}: {reason}")

                    # Tier 3: Trailing stop with volatility adjustment
                    elif pos.highest_price > pos.entry_price:
                        trailing_distance = pos.highest_price * (config.TRAILING_STOP_PERCENT / 100) * (1 + pos.volatility)
                        trailing_stop_price = pos.highest_price - trailing_distance
                        if current_price < trailing_stop_price:
                            should_sell = True
                            reason = f"Trailing Stop {pnl:.1f}%"
                            logger.debug(f"Trailing stop triggered for {mint}: current_price={current_price}, trailing_stop_price={trailing_stop_price}")

                    # Tier 4: Volatility breakout protection
                    elif pos.volatility > 0 and abs(pnl) > (config.STOP_LOSS_PERCENT * 2 * (1 + pos.volatility)):
                        should_sell = True
                        reason = f"Volatility Breakout {pnl:.1f}%"
                        logger.debug(f"Volatility breakout triggered for {mint}: volatility={pos.volatility}, pnl={pnl}")

                    # Tier 5: Time-based exit with volatility-adjusted timing
                    elif held_min >= (240 - (pos.volatility * 60)):  # Adjust hold time based on volatility
                        should_sell = True
                        reason = f"Time Stop {held_min:.0f}m {pnl:.1f}%"
                        logger.debug(f"Time stop triggered for {mint}: held_min={held_min}")

                    # Tier 6: RSI-based exit (if RSI available)
                    elif hasattr(pos, 'rsi') and pos.rsi > 70:  # Overbought condition
                        should_sell = True
                        reason = f"RSI Overbought {pos.rsi:.0f}"
                        logger.debug(f"RSI overbought triggered for {mint}: rsi={pos.rsi}")

                    # Debug logging for decision making
                    logger.debug(f"Position {mint} evaluation - should_sell: {should_sell}, reason: {reason}, current_price: {current_price}, pnl: {pnl:.2f}%")

                    # Additional debug logging for detailed state tracking
                    logger.debug(f"Position {mint} detailed state - token_amount: {pos.token_amount}, current_value_usd: {current_value_usd:.4f}, entry_value_usd: {entry_value_usd:.4f}, volatility: {pos.volatility:.4f}")

                    if should_sell:
                        logger.info(f"Closing position for {mint}: {reason}")
                        await self._close_position(mint, pos, current_price, reason)

                await asyncio.sleep(5)  # Check more frequently for better timing
            except Exception as e:
                logger.error(f"Position monitor error: {e}")
                await asyncio.sleep(20)

    async def _close_position(self, mint: str, pos: Position, current_price: float, reason: str):
        logger.info(f"Closing {pos.token_symbol} | {reason}")

        try:
            ratio = current_price / pos.entry_price

            if ratio > 50 or ratio < 0.02:
                logger.error(
                    f"PRICE ANOMALY {pos.token_symbol} "
                    f"entry={pos.entry_price} "
                    f"current={current_price} "
                    f"ratio={ratio}"
                )
                return

        except Exception as e:
            logger.error(f"Price validation failed: {e}")
            return
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
async def get_sol_usd_price():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                data = await r.json()
                return float(data["solana"]["usd"])
    except Exception:
        return 150.0
    # ============================================================
    # COOLDOWN MODE - Daily loss protection
    # ============================================================
    
    async def _check_cooldown(self) -> bool:
        """Check if bot is in cooldown mode"""
        if not hasattr(self, '_cooldown_until'):
            self._cooldown_until = 0
            self._cooldown_mode = False
        
        if self._cooldown_until and time.time() < self._cooldown_until:
            remaining = int(self._cooldown_until - time.time())
            if remaining % 60 == 0:  # Log setiap menit
                logger.info(f"COOLDOWN: {remaining//60}m remaining")
            return True
        return False

    async def _enter_cooldown(self, duration: int = 300):
        """Enter cooldown mode (default 5 minutes)"""
        self._cooldown_mode = True
        self._cooldown_until = time.time() + duration
        logger.info(f"🛑 COOLDOWN: entered for {duration//60} minutes")
        # Update status
        update_status(last_event=f"COOLDOWN {duration//60}m")

    async def _exit_cooldown(self):
        """Exit cooldown mode"""
        self._cooldown_mode = False
        self._cooldown_until = 0
        logger.info("✅ COOLDOWN: exited, resuming trading")
        update_status(last_event="COOLDOWN EXIT")

    # ============================================================
    # TOKEN PROFILE CACHE
    # ============================================================
    
    async def _get_cached_profile(self, mint: str) -> Optional[Dict]:
        """Get cached token profile if valid"""
        if not hasattr(self, '_profile_cache'):
            self._profile_cache = {}
        
        if mint in self._profile_cache:
            cached_time, data = self._profile_cache[mint]
            if time.time() - cached_time < 300:  # 5 minutes cache
                return data
            else:
                del self._profile_cache[mint]
        return None

    async def _cache_profile(self, mint: str, data: Dict):
        """Cache token profile"""
        if not hasattr(self, '_profile_cache'):
            self._profile_cache = {}
        self._profile_cache[mint] = (time.time(), data)

    # ============================================================
    # EXPONENTIAL BACKOFF untuk 429
    # ============================================================
    
    async def _handle_429(self):
        """Handle rate limit with exponential backoff"""
        if not hasattr(self, '_backoff_delay'):
            self._backoff_delay = 5
            self._last_429 = 0
        
        self._last_429 = time.time()
        delay = self._backoff_delay
        logger.warning(f"⚠️ 429 rate limit: backing off {delay}s")
        await asyncio.sleep(delay)
        
        # Exponential backoff: double delay up to 60s
        self._backoff_delay = min(self._backoff_delay * 2, 60)
        logger.info(f"New backoff delay: {self._backoff_delay}s")
    
    async def _reset_backoff(self):
        """Reset backoff after successful request"""
        if hasattr(self, '_backoff_delay'):
            self._backoff_delay = max(5, self._backoff_delay // 2)
