"""Configuration management for the trading bot."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = LOGS_DIR / "trading_bot.log"


@dataclass(frozen=True)
class BinanceConfig:
    """Binance API credentials and endpoint configuration."""

    api_key: str
    api_secret: str
    base_url: str = FUTURES_TESTNET_BASE_URL

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "BinanceConfig":
        """
        Load configuration from environment variables.

        Args:
            env_path: Optional path to a .env file.

        Returns:
            A validated BinanceConfig instance.

        Raises:
            ValueError: If required environment variables are missing or empty.
        """
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv(PROJECT_ROOT / ".env")

        api_key = os.getenv("BINANCE_API_KEY", "").strip()
        api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

        if not api_key:
            raise ValueError(
                "BINANCE_API_KEY is missing. Copy .env.example to .env and set your keys."
            )
        if not api_secret:
            raise ValueError(
                "BINANCE_API_SECRET is missing. Copy .env.example to .env and set your keys."
            )

        return cls(api_key=api_key, api_secret=api_secret)
