"""
discovery/base.py — kontrak yang harus dipenuhi semua sumber discovery.
"""
from abc import ABC, abstractmethod
from typing import List

from core.models import Token


class DiscoverySource(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch_new_tokens(self) -> List[Token]:
        """Kembalikan daftar token baru sejak polling terakhir. Harus
        menangani error sendiri (return [] kalau gagal, jangan raise
        supaya satu sumber down tidak menjatuhkan seluruh discovery loop)."""
        raise NotImplementedError
