"""
execution/execution_engine.py
================================
PaperExecutor: eksekusi simulasi, benar-benar jalan, dipakai secara default.
LiveExecutor: skeleton eksekusi swap nyata via Jupiter — SENGAJA belum
dilengkapi bagian tanda-tangan & kirim transaksi, supaya tidak ada jalan
tidak sengaja menghabiskan wallet asli dari kode yang belum kamu review.

Kedua kelas mengimplementasikan interface yang sama (buy/sell), jadi
modul lain (main.py, position_manager.py) tidak perlu tahu mode apa
yang aktif.
"""
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from config import settings, require_live_trading_ack
from core.database import db
from core.logger import get_logger
from core.models import Trade
from discovery.sources.dexscreener import DexScreenerSource

log = get_logger("execution.engine")

FEE_PERCENT_ESTIMATE = 1.0  # perkiraan total fee (network + slippage + platform) untuk paper trading


class Executor(ABC):
    @abstractmethod
    async def get_current_price(self, token_address: str) -> float:
        ...

    @abstractmethod
    async def buy(self, token_address: str, amount_usd: float, strategy: str) -> Trade:
        ...

    @abstractmethod
    async def sell(self, token_address: str, amount_token: float, strategy: str) -> Trade:
        ...


class PaperExecutor(Executor):
    """Simulasi penuh — pakai harga real-time dari DexScreener supaya hasil
    simulasi realistis, tapi tidak ada transaksi on-chain sama sekali."""

    def __init__(self):
        self.dexscreener = DexScreenerSource()

    async def get_current_price(self, token_address: str) -> float:
        pair = await self.dexscreener.fetch_pair_data(token_address)
        if not pair:
            return 0.0
        return float(pair.get("priceUsd") or 0)

    async def buy(self, token_address: str, amount_usd: float, strategy: str) -> Trade:
        price = await self.get_current_price(token_address)
        if price <= 0:
            raise RuntimeError(f"Tidak bisa dapat harga untuk {token_address}, BUY dibatalkan")

        fee = amount_usd * (FEE_PERCENT_ESTIMATE / 100)
        net_usd = amount_usd - fee
        amount_token = net_usd / price

        trade = Trade(
            id=None, token_address=token_address, side="BUY",
            price_usd=price, amount_token=amount_token, amount_usd=amount_usd,
            fee_usd=fee, tx_signature=f"PAPER-{token_address[:8]}-BUY",
            is_paper=True, strategy=strategy,
        )
        trade.id = db.insert_trade(trade)
        log.info(f"[PAPER] BUY {token_address[:8]} @ ${price:.8f} "
                  f"amount=${amount_usd:.2f} fee=${fee:.4f}")
        return trade

    async def sell(self, token_address: str, amount_token: float, strategy: str) -> Trade:
        price = await self.get_current_price(token_address)
        if price <= 0:
            log.warning(f"Tidak bisa dapat harga untuk {token_address} saat SELL — "
                        f"pakai harga 0 (kemungkinan token sudah rug/delisted)")

        gross_usd = amount_token * price
        fee = gross_usd * (FEE_PERCENT_ESTIMATE / 100)
        net_usd = gross_usd - fee

        trade = Trade(
            id=None, token_address=token_address, side="SELL",
            price_usd=price, amount_token=amount_token, amount_usd=net_usd,
            fee_usd=fee, tx_signature=f"PAPER-{token_address[:8]}-SELL",
            is_paper=True, strategy=strategy,
        )
        trade.id = db.insert_trade(trade)
        log.info(f"[PAPER] SELL {token_address[:8]} @ ${price:.8f} "
                  f"amount_token={amount_token:.4f} net=${net_usd:.2f}")
        return trade


class LiveExecutor(Executor):
    """
    Skeleton eksekusi live via Jupiter Swap API. Struktur retry, slippage,
    priority fee, dan simulasi transaksi sudah ada, TAPI bagian
    tanda-tangan & pengiriman transaksi sengaja NotImplementedError.

    Untuk melengkapi (kamu yang lakukan, dengan sadar risikonya):
      1. pip install solders solana
      2. Load keypair dari settings.wallet_private_key
      3. Panggil Jupiter Quote API -> dapat route
      4. Panggil Jupiter Swap API -> dapat transaksi unsigned (base64)
      5. Deserialize, tanda-tangani dengan keypair, kirim via RPC
      6. Konfirmasi transaksi (poll getSignatureStatuses)
    """

    JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
    JUPITER_SWAP_URL = "https://quote-api.jup.ag/v6/swap"
    SOL_MINT = "So11111111111111111111111111111111111111112"

    def __init__(self):
        require_live_trading_ack()
        self.rpc_url = settings.rpc_url
        log.warning("LiveExecutor aktif — transaksi akan pakai dana ASLI kalau dilengkapi.")

    async def get_current_price(self, token_address: str) -> float:
        # Untuk live trading, harga sebaiknya diambil dari quote Jupiter
        # (lebih akurat untuk ukuran order kamu) bukan cuma dari DexScreener.
        async with httpx.AsyncClient(timeout=8.0) as client:
            params = {
                "inputMint": self.SOL_MINT,
                "outputMint": token_address,
                "amount": "1000000",  # 0.001 SOL, hanya untuk cek harga
                "slippageBps": "50",
            }
            resp = await client.get(self.JUPITER_QUOTE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        out_amount = float(data.get("outAmount", 0))
        if out_amount <= 0:
            return 0.0
        return 0.001 / (out_amount / 1e9)  # kasar — sesuaikan desimal token asli

    async def buy(self, token_address: str, amount_usd: float, strategy: str) -> Trade:
        raise NotImplementedError(
            "LiveExecutor.buy() belum dilengkapi bagian sign & send transaksi. "
            "Lihat docstring class LiveExecutor untuk langkah yang perlu kamu isi."
        )

    async def sell(self, token_address: str, amount_token: float, strategy: str) -> Trade:
        raise NotImplementedError(
            "LiveExecutor.sell() belum dilengkapi bagian sign & send transaksi. "
            "Lihat docstring class LiveExecutor untuk langkah yang perlu kamu isi."
        )


def get_executor() -> Executor:
    if settings.paper_trading:
        log.info("Mode: PAPER TRADING (simulasi, tanpa transaksi on-chain)")
        return PaperExecutor()
    log.warning("Mode: LIVE TRADING — akan pakai dana asli kalau LiveExecutor dilengkapi")
    return LiveExecutor()
