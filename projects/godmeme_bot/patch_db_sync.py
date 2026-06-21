from pathlib import Path

p = Path("strategy.py")
s = p.read_text()

if "from database import Trade, TradeStatus" not in s:
    s = s.replace(
        "from config import config",
        "from config import config\nfrom database import Trade, TradeStatus"
    )

old = "        self.trade_count += 1\n"

new = """        self.trade_count += 1

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

            except Exception as e:
                logger.error(f"DB BUY failed: {e}")
"""

if "DB BUY saved" not in s:
    s = s.replace(old, new)


old2 = "        self.daily_pnl_sol += pnl_sol\n"

new2 = """        self.daily_pnl_sol += pnl_sol

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

            except Exception as e:
                logger.error(f"DB SELL failed: {e}")
"""

if "DB SELL saved" not in s:
    s = s.replace(old2, new2)

p.write_text(s)
print("PATCH DONE")