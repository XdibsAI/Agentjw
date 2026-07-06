import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sys
import os

import asyncio
import time
import logging

from config import config
from strategy import Strategy
from wallet import wallet
from database import Database
from notifier import Notifier as TelegramNotifier
from status_writer import update_status


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


async def main():

    logger.info("===================================")
    logger.info(" GODMEME BOT STARTING")
    logger.info("===================================")

    logger.info(
        f"Mode: {'PAPER' if config.PAPER_TRADING else 'LIVE'}"
    )

    logger.info(
        f"Wallet: {wallet.public_key}"
    )

    balance = await wallet.get_balance()

    logger.info(
        f"Balance: {balance} SOL"
    )

    update_status(
        mode="paper" if config.PAPER_TRADING else "live",
        start_time=time.strftime("%Y-%m-%d %H:%M:%S"),
        balance=balance,
        daily_pnl=0,
        trades_today=0,
        last_event="Bot started"
    )


    # DATABASE
    db = Database(config.DATABASE_PATH)

    logger.info(
        f"Database: {config.DATABASE_PATH}"
    )


    # TELEGRAM
    notifier = None

    try:
        notifier = TelegramNotifier()
        logger.info("Telegram notifier enabled")
    except Exception as e:
        logger.warning(f"Telegram disabled: {e}")


    strategy = Strategy(
        wallet=wallet,
        jupiter=None,
        raydium_client=None,
        db=db,
        notifier=notifier
    )


    await strategy.run()


if __name__ == "__main__":
    asyncio.run(main())