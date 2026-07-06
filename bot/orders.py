"""Order placement orchestration."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.client import BinanceFuturesClient
from bot.validators import OrderInput, ValidationError, validate_order_input

logger = logging.getLogger("trading_bot.orders")


@dataclass(frozen=True)
class OrderResult:
    """Structured result from a placed order."""

    order_id: int
    status: str
    executed_qty: str
    avg_price: str
    symbol: str
    side: str
    order_type: str
    timestamp: str
    raw_response: dict[str, Any]


class OrderService:
    """Handles validation and execution of futures orders."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        """
        Initialize the order service.

        Args:
            client: Configured Binance Futures client.
        """
        self._client = client

    def validate(self, order_input: OrderInput) -> None:
        """
        Perform additional server-side symbol validation.

        Args:
            order_input: Validated order input.

        Raises:
            ValidationError: If the symbol is not available on testnet.
        """
        logger.info("Validating symbol on exchange | symbol=%s", order_input.symbol)

        if not self._client.symbol_exists(order_input.symbol):
            raise ValidationError(
                f"Symbol '{order_input.symbol}' is not available on Binance Futures Testnet."
            )

        logger.info("Symbol validation passed | symbol=%s", order_input.symbol)

    def place_order(self, order_input: OrderInput) -> OrderResult:
        """
        Place an order on Binance Futures Testnet.

        Args:
            order_input: Validated order parameters.

        Returns:
            Structured OrderResult.

        Raises:
            BinanceAPIException: On API errors.
            BinanceRequestException: On request errors.
        """
        quantity_str = _format_decimal(order_input.quantity)
        price_str = _format_decimal(order_input.price) if order_input.price else None

        response = self._client.create_order(
            symbol=order_input.symbol,
            side=order_input.side,
            order_type=order_input.order_type,
            quantity=quantity_str,
            price=price_str,
        )

        return _build_order_result(response, order_input)

    @staticmethod
    def parse_cli_args(
        symbol: str | None,
        side: str | None,
        order_type: str | None,
        quantity: str | None,
        price: str | None,
    ) -> OrderInput:
        """
        Parse and validate CLI arguments into an OrderInput.

        Args:
            symbol: Trading symbol.
            side: Order side.
            order_type: Order type.
            quantity: Order quantity.
            price: Optional limit price.

        Returns:
            Validated OrderInput.
        """
        return validate_order_input(symbol, side, order_type, quantity, price)


def _format_decimal(value: Decimal) -> str:
    """Format a Decimal without trailing zeros."""
    normalized = value.normalize()
    return format(normalized, "f")


def _build_order_result(response: dict[str, Any], order_input: OrderInput) -> OrderResult:
    """Build an OrderResult from the Binance API response."""
    update_time = response.get("updateTime") or response.get("transactTime")
    if update_time:
        timestamp = datetime.fromtimestamp(update_time / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    else:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    executed_qty = str(response.get("executedQty", "0"))
    avg_price = str(response.get("avgPrice", "0"))

    if order_input.order_type == "MARKET" and (not avg_price or avg_price == "0"):
        cum_quote = response.get("cumQuote")
        if cum_quote and executed_qty and Decimal(executed_qty) > 0:
            avg_price = str(Decimal(cum_quote) / Decimal(executed_qty))

    if order_input.order_type == "LIMIT" and (not avg_price or avg_price == "0"):
        avg_price = str(order_input.price) if order_input.price else "N/A"

    return OrderResult(
        order_id=int(response["orderId"]),
        status=str(response.get("status", "UNKNOWN")),
        executed_qty=executed_qty,
        avg_price=avg_price if avg_price and avg_price != "0" else "N/A",
        symbol=str(response.get("symbol", order_input.symbol)),
        side=str(response.get("side", order_input.side)),
        order_type=str(response.get("type", order_input.order_type)),
        timestamp=timestamp,
        raw_response=response,
    )
