import asyncio
from strategy import Strategy
from wallet import wallet

async def main():
    s = Strategy(
        wallet=wallet,
        jupiter=None,
        raydium_client=None,
        db=None,
        notifier=None
    )

    tokens = await s._scan_new_tokens()

    print("TOTAL TOKENS:", len(tokens))

    for t in tokens[:20]:
        print(
            t["symbol"],
            "liq=", t["liquidity"],
            "vol5m=", t["volume5m"],
            "mcap=", t["mcap"],
            "age=", round(t["age_min"], 2)
        )

asyncio.run(main())