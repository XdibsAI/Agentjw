"""
discovery/discovery_engine.py
===============================
Menggabungkan semua sumber discovery. Tanggung jawab:
  - Deduplikasi lintas sumber (satu token address hanya diproses sekali)
  - Priority queue (token dari sumber lebih cepat/reliable diproses duluan)
  - Cache token yang sudah pernah dilihat (hindari kerja ulang)
  - Retry per-sumber dengan backoff (tenacity)
  - Failover: satu sumber down tidak menjatuhkan sumber lain
"""
import asyncio
import heapq
import itertools
import time
from typing import List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.database import db
from core.logger import get_logger
from core.models import Token
from discovery.base import DiscoverySource
from discovery.sources.dexscreener import DexScreenerSource
from discovery.sources.birdeye import BirdeyeSource
from discovery.sources.pumpfun import PumpFunSource
from discovery.sources.raydium import RaydiumSource

log = get_logger("discovery.engine")

# Prioritas sumber — makin kecil angka, makin diprioritaskan (dianggap
# makin cepat/segar). Pump.fun & Raydium (kalau sudah diisi) idealnya
# paling cepat karena native on-chain listener, DexScreener/Birdeye agregator.
SOURCE_PRIORITY = {
    "pumpfun": 0,
    "raydium": 1,
    "dexscreener": 2,
    "birdeye": 3,
}


class DiscoveryEngine:
    def __init__(self, poll_interval_seconds: float = 5.0):
        self.poll_interval = poll_interval_seconds
        self.sources: List[DiscoverySource] = [
            PumpFunSource(),
            RaydiumSource(),
            DexScreenerSource(),
            BirdeyeSource(),
        ]
        self._queue: List[tuple] = []   # heap of (priority, counter, Token)
        self._counter = itertools.count()
        self._cache: set = set()        # token address sudah pernah masuk antrian

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=False,
    )
    async def _poll_source(self, source: DiscoverySource) -> List[Token]:
        return await source.fetch_new_tokens()

    async def poll_once(self) -> int:
        """Poll semua sumber sekali, masukkan token baru (belum di-cache)
        ke priority queue. Return jumlah token baru yang masuk."""
        added = 0
        results = await asyncio.gather(
            *[self._safe_poll(s) for s in self.sources],
            return_exceptions=False,
        )
        for source, tokens in zip(self.sources, results):
            priority = SOURCE_PRIORITY.get(source.name, 99)
            for token in tokens:
                if token.address in self._cache or db.token_exists(token.address):
                    continue
                self._cache.add(token.address)
                heapq.heappush(self._queue, (priority, next(self._counter), token))
                db.upsert_token(token)
                added += 1
        if added:
            log.info(f"discovery: {added} token baru masuk antrian (total queue={len(self._queue)})")
        return added

    async def _safe_poll(self, source: DiscoverySource) -> List[Token]:
        try:
            return await self._poll_source(source)
        except Exception as e:
            log.error(f"sumber '{source.name}' gagal setelah retry: {e}")
            return []

    def pop_next(self) -> Optional[Token]:
        """Ambil token prioritas tertinggi dari queue, atau None kalau kosong."""
        if not self._queue:
            return None
        _, _, token = heapq.heappop(self._queue)
        return token

    def queue_size(self) -> int:
        return len(self._queue)

    async def run_forever(self, on_token_callback):
        """Loop utama discovery: poll berkala, proses semua token di queue
        lewat callback (biasanya pipeline analyzer -> scoring -> decision)."""
        log.info(f"DiscoveryEngine mulai — poll setiap {self.poll_interval}s, "
                  f"sumber aktif: {[s.name for s in self.sources]}")
        while True:
            start = time.monotonic()
            await self.poll_once()
            while True:
                token = self.pop_next()
                if token is None:
                    break
                try:
                    await on_token_callback(token)
                except Exception as e:
                    log.error(f"error memproses token {token.address}: {e}")
            elapsed = time.monotonic() - start
            await asyncio.sleep(max(0.0, self.poll_interval - elapsed))
