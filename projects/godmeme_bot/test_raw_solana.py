import aiohttp
import asyncio
import time

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.dexscreener.com/latest/dex/search?q=solana"
        ) as r:
            data = await r.json()

    pairs = data.get("pairs", [])

    solana = []

    for pair in pairs:
        if pair.get("chainId") == "solana":
            solana.append({
                "symbol": pair.get("baseToken", {}).get("symbol"),
                "mint": pair.get("baseToken", {}).get("address"),
                "liq": pair.get("liquidity", {}).get("usd"),
                "vol5m": pair.get("volume", {}).get("m5"),
                "mcap": pair.get("marketCap"),
                "dex": pair.get("dexId"),
                "created": pair.get("pairCreatedAt")
            })

    print("SOLANA PAIRS:", len(solana))

    for x in solana[:20]:
        print(x)

asyncio.run(main())