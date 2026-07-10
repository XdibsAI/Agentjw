"""
discovery/sources/pumpfun.py
=============================
STUB — Pump.fun tidak punya REST API resmi publik yang stabil. Sumber
paling reliable adalah subscribe ke event program on-chain mereka lewat
Solana WebSocket (logsSubscribe / geyser plugin), yang butuh RPC provider
dengan geyser (Helius, Triton, dst) — bukan RPC publik gratisan.

Struktur di bawah ini siap dipakai; bagian yang butuh koneksi geyser
sengaja saya beri TODO supaya kamu isi dengan provider RPC yang kamu pakai.
"""
from typing import List

from core.logger import get_logger
from core.models import Token
from discovery.base import DiscoverySource

log = get_logger("discovery.pumpfun")

PUMPFUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"  # program pump.fun


class PumpFunSource(DiscoverySource):
    name = "pumpfun"

    def __init__(self):
        self._ws = None  # TODO: inisialisasi koneksi geyser/websocket di sini

    async def fetch_new_tokens(self) -> List[Token]:
        # TODO: implementasikan subscribe ke PUMPFUN_PROGRAM_ID via geyser
        # websocket dari provider RPC kamu (mis. Helius "enhanced websockets"),
        # lalu parse instruksi "create" jadi Token(...).
        #
        # Karena ini butuh provider berbayar dan kredensial spesifik kamu,
        # sumber ini mengembalikan list kosong sampai kamu lengkapi.
        log.debug("PumpFunSource belum diimplementasikan penuh — lihat TODO di file ini")
        return []
