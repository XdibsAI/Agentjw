"""
discovery/sources/birdeye.py
=============================
STUB — Birdeye butuh API key berbayar (https://docs.birdeye.so). Struktur
sudah lengkap, tinggal isi BIRDEYE_API_KEY di .env dan implementasikan
parsing response sesuai schema Birdeye yang aktif saat kamu pakai (schema
mereka pernah berubah, jangan asumsikan field di bawah ini masih akurat —
cek docs resmi dulu).
"""
from typing import List

import httpx

from config import settings
from core.logger import get_logger
from core.models import Token
from discovery.base import DiscoverySource

log = get_logger("discovery.birdeye")

BASE_URL = "https://public-api.birdeye.so"


class BirdeyeSource(DiscoverySource):
    name = "birdeye"

    def __init__(self):
        self.api_key = settings.birdeye_api_key
        self._seen: set = set()

    async def fetch_new_tokens(self) -> List[Token]:
        if not self.api_key:
            log.debug("BIRDEYE_API_KEY kosong — sumber birdeye di-skip")
            return []

        headers = {"X-API-KEY": self.api_key, "x-chain": "solana"}
        # TODO: sesuaikan endpoint dengan docs Birdeye terbaru sebelum dipakai.
        # Endpoint contoh (VERIFIKASI DULU sebelum production):
        url = f"{BASE_URL}/defi/v2/tokens/new_listing"
        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            log.warning(f"gagal fetch birdeye: {e}")
            return []

        tokens: List[Token] = []
        for item in data.get("data", {}).get("items", []):
            address = item.get("address")
            if not address or address in self._seen:
                continue
            self._seen.add(address)
            tokens.append(Token(
                address=address,
                symbol=item.get("symbol", "?"),
                name=item.get("name", "unknown"),
                source=self.name,
                raw=item,
            ))
        return tokens
