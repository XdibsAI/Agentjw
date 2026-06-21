import os
import json
import base64
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.system_program import transfer, TransferParams
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    IS_PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    
    # Solana RPC
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    SOLANA_WS_URL = os.getenv('SOLANA_WS_URL', 'wss://api.mainnet-beta.solana.com')
    
    # Wallet
    WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY')
    WALLET_PUBLIC_KEY = os.getenv('WALLET_PUBLIC_KEY')

class JupiterClient:
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6"
        self.async_client = AsyncClient(Config.SOLANA_RPC_URL)
        if Config.WALLET_PRIVATE_KEY:
            private_key_bytes = base64.b64decode(Config.WALLET_PRIVATE_KEY)
            self.wallet = Keypair.from_bytes(private_key_bytes)
        else:
            self.wallet = None

    async def get_quote(self, input_mint: str, output_mint: str, amount: int) -> Dict[str, Any]:
        """Get a quote for swapping tokens"""
        url = f"{self.base_url}/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': 50  # 0.5% slippage
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def execute_swap(self, quote: Dict[str, Any]) -> Optional[str]:
        """Execute a swap transaction"""
        if Config.IS_PAPER_TRADING:
            print("Paper trading mode: Skipping actual swap execution")
            return "PAPER_TRADE_SIMULATION"
            
        if not self.wallet:
            raise Exception("Wallet not configured")
            
        # Get serialized transaction
        url = f"{self.base_url}/swap"
        payload = {
            "quoteResponse": quote,
            "userPublicKey": str(self.wallet.pubkey()),
            "wrapAndUnwrapSol": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                swap_response = await response.json()
                
        if "error" in swap_response:
            raise Exception(f"Swap error: {swap_response['error']}")
            
        # Deserialize and sign transaction
        raw_tx = swap_response["swapTransaction"]
        tx_bytes = base64.b64decode(raw_tx)
        transaction = Transaction.deserialize(tx_bytes)
        transaction.sign(self.wallet)
        
        # Send transaction
        opts = TxOpts(skip_preflight=True, preflight_commitment="confirmed")
        result = await self.async_client.send_raw_transaction(
            transaction.serialize(), 
            opts
        )
        return str(result.value)

    async def get_token_price(self, mint: str) -> float:
        """Get token price in SOL"""
        # For SOL
        if mint == "So11111111111111111111111111111111111111112":
            return 1.0
            
        # Get quote for 1000000000 units (1 SOL worth of lamports) to token
        quote = await self.get_quote(
            "So11111111111111111111111111111111111111112", 
            mint, 
            1000000000
        )
        
        if "error" in quote:
            raise Exception(f"Price error: {quote['error']}")
            
        # Calculate price per unit
        out_amount = int(quote["outAmount"])
        in_amount = int(quote["inAmount"])
        return in_amount / out_amount / 1e9

# Example usage
async def main():
    client = JupiterClient()
    
    # Example: Get price of a token
    try:
        price = await client.get_token_price("EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm")  # SHDW token
        print(f"Token price: {price} SOL")
        
        # Example: Get quote
        quote = await client.get_quote(
            "So11111111111111111111111111111111111111112",  # SOL
            "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",  # SHDW
            100000000  # 0.1 SOL
        )
        print(f"Quote: {quote}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())