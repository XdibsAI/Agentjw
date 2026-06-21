import os
import logging
import asyncio
import aiohttp
import json
from typing import Optional
from config import config

logger = logging.getLogger(__name__)

SOL_MINT = "So11111111111111111111111111111111111111112"

class Wallet:
    def __init__(self):
        self.keypair = None
        self.public_key = None
        self._balance_cache = None
        self._balance_time = 0
        self._init_keypair()

    def _init_keypair(self):
        try:
            from solders.keypair import Keypair
            import base58
            pk = config.SOLANA_PRIVATE_KEY.strip()
            if not pk:
                logger.warning("SOLANA_PRIVATE_KEY not set - using paper mode")
                self.public_key = "PAPER_TRADING_MODE"
                return
            raw = base58.b58decode(pk)
            self.keypair = Keypair.from_bytes(raw)
            self.public_key = str(self.keypair.pubkey())
            logger.info(f"Wallet loaded: {self.public_key[:8]}...{self.public_key[-4:]}")
        except Exception as e:
            logger.error(f"Wallet init failed: {e}")
            self.public_key = "PAPER_TRADING_MODE"

    async def get_balance(self) -> float:
        import time
        if self._balance_cache and time.time() - self._balance_time < 30:
            return self._balance_cache
        try:
            if config.PAPER_TRADING or not self.keypair:
                # Load balance from paper_wallet.json
                paper_file = "paper_wallet.json"
                if os.path.exists(paper_file):
                    try:
                        with open(paper_file, 'r') as f:
                            data = json.load(f)
                            return float(data.get("balance", 10.0))
                    except Exception as e:
                        logger.error(f"Failed to read paper wallet: {e}")
                return 10.0  # Default paper balance
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0", "id": 1,
                    "method": "getBalance",
                    "params": [self.public_key, {"commitment": "confirmed"}]
                }
                async with session.post(config.get_rpc(), json=payload, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    data = await r.json()
                    lamports = data.get("result", {}).get("value", 0)
                    balance = lamports / 1e9
                    self._balance_cache = balance
                    self._balance_time = time.time()
                    return balance
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            return self._balance_cache or 0.0

    async def sign_and_send(self, transaction_bytes: bytes) -> Optional[str]:
        if config.PAPER_TRADING:
            import uuid
            tx_hash = "PAPER_" + str(uuid.uuid4())[:8]
            logger.info(f"[PAPER] Trade executed: {tx_hash}")
            return tx_hash
        try:
            from solders.transaction import VersionedTransaction
            import base64
            tx = VersionedTransaction.from_bytes(transaction_bytes)
            tx.sign([self.keypair])
            tx_bytes = base64.b64encode(bytes(tx)).decode()
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0", "id": 1,
                    "method": "sendTransaction",
                    "params": [tx_bytes, {"encoding": "base64", "skipPreflight": False, "maxRetries": 3}]
                }
                async with session.post(config.get_rpc(), json=payload, timeout=aiohttp.ClientTimeout(total=30)) as r:
                    data = await r.json()
                    if "result" in data:
                        # Invalidate balance cache after successful transaction
                        self._balance_cache = None
                        self._balance_time = 0
                        return data["result"]
                    logger.error(f"TX error: {data.get('error')}")
                    return None
        except Exception as e:
            logger.error(f"Sign/send failed: {e}")
            return None

    async def update_paper_balance(self, new_balance: float):
        """Update paper wallet balance in paper_wallet.json"""
        if config.PAPER_TRADING:
            paper_file = "paper_wallet.json"
            try:
                data = {}
                if os.path.exists(paper_file):
                    with open(paper_file, 'r') as f:
                        data = json.load(f)
                data["balance"] = new_balance
                data["last_updated"] = asyncio.get_event_loop().time()
                with open(paper_file, 'w') as f:
                    json.dump(data, f)
                # Update cache
                self._balance_cache = new_balance
                self._balance_time = asyncio.get_event_loop().time()
            except Exception as e:
                logger.error(f"Failed to update paper wallet: {e}")

    async def sync_paper_balance_after_sell(self, sold_amount: float, price: float):
        """Sync paper wallet balance after SELL transaction"""
        if config.PAPER_TRADING:
            try:
                proceeds = sold_amount * price
                current_balance = await self.get_balance()
                new_balance = current_balance + proceeds
                await self.update_paper_balance(new_balance)
                logger.info(f"Paper wallet balance synced after SELL: {new_balance:.6f} SOL")
            except Exception as e:
                logger.error(f"Failed to sync paper balance after SELL: {e}")

wallet = Wallet()