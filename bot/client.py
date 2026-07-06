"""Binance Futures Testnet client wrapper."""

import logging
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.config import BinanceConfig, FUTURES_TESTNET_BASE_URL

logger = logging.getLogger("trading_bot.client")


class BinanceFuturesClient:
    """Wrapper around python-binance for Futures Testnet operations."""

    def __init__(self, config: BinanceConfig) -> None:
        """
        Initialize the Binance Futures Testnet client.

        Args:
            config: Binance API configuration.
        """
        self._config = config
        self._client = Client(config.api_key, config.api_secret, testnet=True)
        self._client.FUTURES_URL = f"{FUTURES_TESTNET_BASE_URL}/fapi"
        logger.info("Binance Futures Testnet client initialized | base_url=%s", config.base_url)

    def ping(self) -> bool:
        """
        Verify connectivity to Binance Futures Testnet.

        Returns:
            True if the server responds successfully.
        """
        logger.debug("Sending ping request to Binance Futures Testnet")
        self._client.futures_ping()
        logger.debug("Ping successful")
        return True

    def get_exchange_info(self) -> dict[str, Any]:
        """
        Fetch futures exchange information.

        Returns:
            Exchange info dictionary from Binance API.
        """
        logger.debug("Fetching futures exchange info")
        info = self._client.futures_exchange_info()
        logger.debug("Exchange info fetched | symbols=%d", len(info.get("symbols", [])))
        return info

    def symbol_exists(self, symbol: str) -> bool:
        """
        Check whether a symbol is listed on Futures Testnet.

        Args:
            symbol: Trading pair symbol.

        Returns:
            True if the symbol exists and is tradable.
        """
        info = self.get_exchange_info()
        for entry in info.get("symbols", []):
            if entry.get("symbol") == symbol and entry.get("status") == "TRADING":
                return True
        return False

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str | None = None,
    ) -> dict[str, Any]:
        """
        Place a futures order on Binance Testnet.

        Args:
            symbol: Trading pair symbol.
            side: BUY or SELL.
            order_type: MARKET or LIMIT.
            quantity: Order quantity as string.
            price: Limit price as string (required for LIMIT orders).

        Returns:
            Order response dictionary from Binance API.

        Raises:
            BinanceAPIException: On API-level errors.
            BinanceRequestException: On request-level errors.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"

        logger.info("Placing order | params=%s", params)

        try:
            response = self._client.futures_create_order(**params)
            logger.info("Order placed successfully | orderId=%s", response.get("orderId"))
            logger.debug("Full API response: %s", response)
            return response
        except BinanceAPIException as exc:
            logger.error(
                "Binance API error | code=%s | message=%s",
                exc.code,
                exc.message,
            )
            raise
        except BinanceRequestException as exc:
            logger.error("Binance request error | status=%s | message=%s", exc.status_code, exc.message)
            raise
