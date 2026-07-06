"""Input validation for CLI arguments and order parameters."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

VALID_SIDES = frozenset({"BUY", "SELL"})
VALID_ORDER_TYPES = frozenset({"MARKET", "LIMIT"})


@dataclass(frozen=True)
class OrderInput:
    """Validated order parameters from CLI input."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None


class ValidationError(Exception):
    """Raised when user input fails validation."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _parse_positive_decimal(value: str, field_name: str) -> Decimal:
    """Parse a string into a positive Decimal."""
    try:
        decimal_value = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValidationError(
            f"Invalid {field_name}: '{value}' is not a valid number."
        ) from None

    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be greater than 0. Received: {value}.")

    return decimal_value


def validate_symbol(symbol: str | None) -> str:
    """
    Validate and normalize a trading symbol.

    Args:
        symbol: Raw symbol string from CLI.

    Returns:
        Uppercase symbol string.

    Raises:
        ValidationError: If symbol is missing or invalid.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("--symbol is required. Example: --symbol BTCUSDT")

    normalized = symbol.strip().upper()

    if len(normalized) < 3:
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Symbol must be at least 3 characters."
        )

    if not normalized.isalnum():
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Symbol must contain only letters and numbers."
        )

    return normalized


def validate_side(side: str | None) -> str:
    """
    Validate order side.

    Args:
        side: Raw side string from CLI.

    Returns:
        Uppercase side string (BUY or SELL).

    Raises:
        ValidationError: If side is missing or invalid.
    """
    if not side or not side.strip():
        raise ValidationError("--side is required. Allowed values: BUY, SELL")

    normalized = side.strip().upper()

    if normalized not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Allowed values: BUY, SELL"
        )

    return normalized


def validate_order_type(order_type: str | None) -> str:
    """
    Validate order type.

    Args:
        order_type: Raw order type string from CLI.

    Returns:
        Uppercase order type string (MARKET or LIMIT).

    Raises:
        ValidationError: If order type is missing or invalid.
    """
    if not order_type or not order_type.strip():
        raise ValidationError("--type is required. Allowed values: MARKET, LIMIT")

    normalized = order_type.strip().upper()

    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Allowed values: MARKET, LIMIT"
        )

    return normalized


def validate_order_input(
    symbol: str | None,
    side: str | None,
    order_type: str | None,
    quantity: str | None,
    price: str | None,
) -> OrderInput:
    """
    Validate all CLI order arguments.

    Args:
        symbol: Trading pair symbol.
        side: Order side (BUY/SELL).
        order_type: Order type (MARKET/LIMIT).
        quantity: Order quantity as string.
        price: Limit price as string (required for LIMIT orders).

    Returns:
        Validated OrderInput instance.

    Raises:
        ValidationError: If any argument is missing or invalid.
    """
    validated_symbol = validate_symbol(symbol)
    validated_side = validate_side(side)
    validated_type = validate_order_type(order_type)

    if not quantity or not str(quantity).strip():
        raise ValidationError("--quantity is required and must be greater than 0.")

    validated_quantity = _parse_positive_decimal(str(quantity), "Quantity")

    validated_price: Decimal | None = None

    if validated_type == "LIMIT":
        if not price or not str(price).strip():
            raise ValidationError(
                "--price is required for LIMIT orders and must be greater than 0."
            )
        validated_price = _parse_positive_decimal(str(price), "Price")
    elif price is not None and str(price).strip():
        raise ValidationError(
            "--price should only be provided for LIMIT orders. "
            "Remove --price for MARKET orders."
        )

    return OrderInput(
        symbol=validated_symbol,
        side=validated_side,
        order_type=validated_type,
        quantity=validated_quantity,
        price=validated_price,
    )
