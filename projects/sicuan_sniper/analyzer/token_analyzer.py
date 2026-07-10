"""
analyzer/token_analyzer.py
============================
Analisis per-token. Menggabungkan data dari DexScreener (liquidity, volume,
age, pair info) dengan pengecekan on-chain via Solana RPC (mint authority,
freeze authority) lewat JSON-RPC langsung (tanpa dependency SDK berat).

Field yang TIDAK bisa diisi otomatis dengan akurat (creator history,
smart money detection, whale activity, fresh wallet ratio) diberi nilai
default konservatif + risk_flag, bukan di-fake seolah-olah dianalisis.
Kalau kamu mau ini akurat, perlu integrasi indexer wallet-labeling
(mis. Helius, SolanaFM) yang butuh API key/subscription sendiri.
"""
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import settings
from core.logger import get_logger
from core.models import AnalysisResult, Token
from discovery.sources.dexscreener import DexScreenerSource

log = get_logger("analyzer.token")


class TokenAnalyzer:
    def __init__(self):
        self.dexscreener = DexScreenerSource()
        self.rpc_url = settings.rpc_url

    async def analyze(self, token: Token) -> AnalysisResult:
        pair = await self.dexscreener.fetch_pair_data(token.address)
        result = AnalysisResult(token_address=token.address)

        if pair:
            self._fill_from_pair(result, pair)
        else:
            result.risk_flags.append("no_pair_data")

        await self._check_mint_freeze_authority(result, token.address)

        self._derive_risk_flags(result)
        return result

    def _fill_from_pair(self, result: AnalysisResult, pair: dict) -> None:
        liquidity = pair.get("liquidity") or {}
        result.liquidity_usd = float(liquidity.get("usd") or 0)

        result.fdv_usd = float(pair.get("fdv") or 0)
        result.market_cap_usd = float(pair.get("marketCap") or pair.get("fdv") or 0)

        volume = pair.get("volume") or {}
        result.volume_5m_usd = float(volume.get("m5") or 0)
        result.volume_1h_usd = float(volume.get("h1") or 0)

        txns = pair.get("txns", {}).get("m5", {})
        buys = float(txns.get("buys") or 0)
        sells = float(txns.get("sells") or 1)  # hindari div-by-zero
        result.buy_sell_ratio_5m = buys / sells if sells else buys

        created_at_ms = pair.get("pairCreatedAt")
        if created_at_ms:
            created = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)
            age = datetime.now(timezone.utc) - created
            result.age_minutes = age.total_seconds() / 60.0

        info = pair.get("info") or {}
        socials = {s.get("type", "unknown"): True for s in info.get("socials", [])}
        result.social_signals = {
            "website": bool(info.get("websites")),
            "twitter": socials.get("twitter", False),
            "telegram": socials.get("telegram", False),
        }

    async def _check_mint_freeze_authority(self, result: AnalysisResult, mint_address: str) -> None:
        """Cek mint authority & freeze authority lewat getAccountInfo RPC.
        Kalau authority-nya null, artinya sudah di-revoke (lebih aman)."""
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getAccountInfo",
            "params": [mint_address, {"encoding": "jsonParsed"}],
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(self.rpc_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            parsed = (
                data.get("result", {})
                    .get("value", {})
                    .get("data", {})
                    .get("parsed", {})
                    .get("info", {})
            )
            result.mint_authority_revoked = parsed.get("mintAuthority") is None
            result.freeze_authority_revoked = parsed.get("freezeAuthority") is None
        except Exception as e:
            log.warning(f"gagal cek mint/freeze authority {mint_address}: {e}")
            # konservatif: anggap BELUM revoked kalau gagal cek (aman > asumsi baik)
            result.mint_authority_revoked = False
            result.freeze_authority_revoked = False
            result.risk_flags.append("authority_check_failed")

    def _derive_risk_flags(self, result: AnalysisResult) -> None:
        if result.liquidity_usd < settings.min_liquidity_usd:
            result.risk_flags.append("liquidity_below_minimum")
        if not result.mint_authority_revoked:
            result.risk_flags.append("mint_authority_active")
        if not result.freeze_authority_revoked:
            result.risk_flags.append("freeze_authority_active")
        if result.volume_5m_usd < settings.min_volume_5m_usd:
            result.risk_flags.append("volume_below_minimum")
        if result.age_minutes and result.age_minutes < 2:
            result.risk_flags.append("extremely_new_high_risk")
