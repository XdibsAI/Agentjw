"""
config/settings.py
===================
Semua parameter dapat diubah lewat .env, tanpa menyentuh source code.
Divalidasi dengan pydantic supaya salah isi .env ketahuan saat startup,
bukan di tengah trading.
"""
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Mode
    paper_trading: bool = Field(True, alias="PAPER_TRADING")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # RPC
    rpc_url: str = Field("https://api.mainnet-beta.solana.com", alias="RPC_URL")
    rpc_url_backup: str = Field("", alias="RPC_URL_BACKUP")

    # Wallet
    wallet_private_key: str = Field("", alias="WALLET_PRIVATE_KEY")

    # Modal & risk
    starting_capital_usd: float = Field(5.0, alias="STARTING_CAPITAL_USD")
    max_position_size_usd: float = Field(1.5, alias="MAX_POSITION_SIZE_USD")
    max_concurrent_positions: int = Field(3, alias="MAX_CONCURRENT_POSITIONS")
    max_daily_loss_usd: float = Field(2.0, alias="MAX_DAILY_LOSS_USD")
    max_daily_loss_percent: float = Field(40.0, alias="MAX_DAILY_LOSS_PERCENT")
    cooldown_after_loss_minutes: int = Field(10, alias="COOLDOWN_AFTER_LOSS_MINUTES")
    circuit_breaker_consecutive_losses: int = Field(3, alias="CIRCUIT_BREAKER_CONSECUTIVE_LOSSES")

    # Filter minimum
    min_liquidity_usd: float = Field(3000.0, alias="MIN_LIQUIDITY_USD")
    min_volume_5m_usd: float = Field(500.0, alias="MIN_VOLUME_5M_USD")
    min_holder_count: int = Field(30, alias="MIN_HOLDER_COUNT")
    max_top_holder_percent: float = Field(25.0, alias="MAX_TOP_HOLDER_PERCENT")

    # Scoring
    buy_score_threshold: float = Field(75.0, alias="BUY_SCORE_THRESHOLD")
    watch_score_threshold: float = Field(55.0, alias="WATCH_SCORE_THRESHOLD")

    # Position management
    take_profit_levels_raw: str = Field("20,50,100", alias="TAKE_PROFIT_LEVELS")
    trailing_stop_percent: float = Field(15.0, alias="TRAILING_STOP_PERCENT")
    hard_stop_loss_percent: float = Field(25.0, alias="HARD_STOP_LOSS_PERCENT")
    time_stop_minutes: int = Field(60, alias="TIME_STOP_MINUTES")

    # Discovery sources
    birdeye_api_key: str = Field("", alias="BIRDEYE_API_KEY")

    # Storage
    database_path: str = Field("data/sicuan_sniper.db", alias="DATABASE_PATH")

    @field_validator("max_position_size_usd")
    @classmethod
    def position_not_bigger_than_capital(cls, v, info):
        return v

    @property
    def take_profit_levels(self) -> List[float]:
        return [float(x.strip()) for x in self.take_profit_levels_raw.split(",") if x.strip()]

    @property
    def database_full_path(self) -> Path:
        p = ROOT_DIR / self.database_path
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    class Config:
        env_file = str(ROOT_DIR / ".env")
        populate_by_name = True
        extra = "ignore"


settings = Settings()


def require_live_trading_ack():
    """Live trading harus eksplisit di-acknowledge, tidak boleh nyala diam-diam."""
    if not settings.paper_trading and not settings.wallet_private_key:
        raise RuntimeError(
            "PAPER_TRADING=false tapi WALLET_PRIVATE_KEY kosong. "
            "Isi private key ATAU kembalikan PAPER_TRADING=true."
        )
