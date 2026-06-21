import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Solana
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY','')}"
    SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY", "")
    
    # Use Helius if available, else fallback
    @classmethod
    def get_rpc(cls):
        if os.getenv("HELIUS_API_KEY"):
            return cls.HELIUS_RPC_URL
        return cls.SOLANA_RPC_URL

    # Trading mode
    PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
    LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"

    # Risk
    DEFAULT_POSITION_SIZE_SOL = float(os.getenv("DEFAULT_POSITION_SIZE_SOL", "0.1"))
    MAX_DAILY_LOSS_SOL = float(os.getenv("MAX_DAILY_LOSS_SOL", "1.0"))
    MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
    STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "30"))
    TAKE_PROFIT_MULTIPLIER = float(os.getenv("TAKE_PROFIT_MULTIPLIER", "2.0"))
    SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", "1500"))

    # Filters
    MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "10000"))
    MIN_VOLUME_5M_USD = float(os.getenv("MIN_VOLUME_5M_USD", "5000"))
    MAX_MCAP_USD = float(os.getenv("MAX_MCAP_USD", "5000000"))

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # OpenRouter
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-coder")

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./godmeme.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()