"""
discovery/sources/raydium.py
==============================
STUB — pool baru Raydium paling reliable dideteksi lewat DexScreener
(sudah di-cover DexScreenerSource dengan chain_id filter) atau lewat
indexer on-chain sendiri (mendengarkan instruksi initialize2 program
Raydium AMM). Placeholder ini untuk kalau kamu nanti mau indexer sendiri
yang lebih cepat dari DexScreener (mereka ada delay beberapa detik-menit).
"""
from typing import List

from core.logger import get_logger
from core.models import Token
from discovery.base import DiscoverySource

log = get_logger("discovery.raydium")

RAYDIUM_AMM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"


class RaydiumSource(DiscoverySource):
    name = "raydium"

    async def fetch_new_tokens(self) -> List[Token]:
        # TODO: subscribe ke logs program Raydium AMM lewat websocket RPC,
        # parse instruksi initialize2 untuk dapat pool baru secepat mungkin.
        # Untuk sekarang, DexScreenerSource sudah mencakup pool Raydium
        # (dengan delay lebih besar) — sumber ini kosong sampai diisi.
        log.debug("RaydiumSource belum diimplementasikan penuh — lihat TODO di file ini")
        return []
