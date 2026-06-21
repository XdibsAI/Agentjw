import aiohttp
import asyncio

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get(
            "https://api.dexscreener.com/latest/dex/search?q=solana"
        ) as r:
            data = await r.json()

    pairs = data.get("pairs", [])

    print("TOTAL:", len(pairs))

    for p in pairs[:30]:
        print(
            p.get("chainId"),
            p.get("dexId"),
            p.get("baseToken", {}).get("symbol")
        )

asyncio.run(main())