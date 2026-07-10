"""
discovery/sources/dexscreener.py
=================================
Sumber discovery NYATA — pakai public API DexScreener (tidak butuh API key).
Docs: https://docs.dexscreener.com/api/reference

Endpoint yang dipakai: token-profiles/latest untuk sinyal token baru, lalu
detail pair lewat /latest/dex/tokens/{address} untuk data liquidity/volume.
"""
from typing import List

import httpx

from core.logger import get_logger
from core.models import Token
from discovery.base import DiscoverySource

log = get_logger("discovery.dexscreener")

LATEST_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
PAIRS_BY_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/{address}"


class DexScreenerSource(DiscoverySource):
    name = "dexscreener"

    def __init__(self, chain_id: str = "solana", timeout: float = 8.0):
        self.chain_id = chain_id
        self.timeout = timeout
        self._seen: set = set()

    async def fetch_new_tokens(self) -> List[Token]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(LATEST_PROFILES_URL)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            log.warning(f"gagal fetch dexscreener profiles: {e}")
            return []

        tokens: List[Token] = []
        items = data if isinstance(data, list) else data.get("pairs", [])
        for item in items:
            if item.get("chainId") != self.chain_id:
                continue
            address = item.get("tokenAddress") or item.get("address")
            if not address or address in self._seen:
                continue
            self._seen.add(address)
            tokens.append(Token(
                address=address,
                symbol=(item.get("symbol") or "?")[:16],
                name=item.get("name") or item.get("description", "")[:64] or "unknown",
                source=self.name,
                raw=item,
            ))
        return tokens

    async def fetch_pair_data(self, token_address: str) -> dict:
        """Ambil data pair (liquidity, volume, price) untuk satu token —
        dipakai oleh TokenAnalyzer."""
        url = PAIRS_BY_TOKEN_URL.format(address=token_address)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            log.warning(f"gagal fetch pair data {token_address}: {e}")
            return {}

        pairs = data.get("pairs") or []
        if not pairs:
            return {}
        # ambil pair dengan liquidity tertinggi (biasanya pair utama)
        best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd", 0) or 0)
        return best
