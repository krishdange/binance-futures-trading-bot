#!/usr/bin/env python3
"""Command-line interface for the Binance Futures Testnet trading bot."""

import argparse
import logging
import sys
from pathlib import Path

from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.client import BinanceFuturesClient
from bot.config import BinanceConfig
from bot.logging_config import setup_logging
from bot.orders import OrderService
from bot.utils import (
    confirm_proceed,
    execution_timer,
    print_error_banner,
    print_header,
    print_info,
    print_order_summary,
    print_success_banner,
    spinner,
)
from bot.validators import ValidationError

logger = logging.getLogger("trading_bot")


def build_parser() -> argparse.ArgumentParser:
    """
    Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place Futures orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01\n"
            "  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 2500\n"
        ),
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol (e.g. BTCUSDT)",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        choices=["MARKET", "LIMIT", "market", "limit"],
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity (must be > 0)",
    )
    parser.add_argument(
        "--price",
        default=None,
        help="Limit price (required for LIMIT orders, must be > 0)",
    )

    return parser


def _log_cli_arguments(args: argparse.Namespace) -> None:
    """Log parsed CLI arguments."""
    logger.info(
        "CLI arguments | symbol=%s | side=%s | type=%s | quantity=%s | price=%s",
        args.symbol,
        args.side,
        args.order_type,
        args.quantity,
        args.price,
    )


def _handle_binance_api_error(exc: BinanceAPIException) -> str:
    """Convert BinanceAPIException to a user-friendly message."""
    code = exc.code
    message = exc.message

    known_messages = {
        -2019: "Insufficient margin balance. Fund your Futures Testnet wallet and try again.",
        -2010: "Order would immediately trigger. Adjust your price or quantity.",
        -1111: "Invalid precision for quantity or price. Check symbol filters on testnet.",
        -1121: "Invalid symbol. Verify the symbol exists on Binance Futures Testnet.",
        -1102: "A required parameter is missing or invalid.",
        -1021: "Timestamp sync issue. Check your system clock and try again.",
        -2015: "Invalid API key or permissions. Verify your testnet API keys.",
    }

    friendly = known_messages.get(code)
    if friendly:
        return friendly

    return f"Binance API error (code {code}): {message}"


def _handle_binance_request_error(exc: BinanceRequestException) -> str:
    """Convert BinanceRequestException to a user-friendly message."""
    return (
        f"Failed to reach Binance Futures Testnet "
        f"(HTTP {exc.status_code}): {exc.message}"
    )


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the trading bot CLI.

    Args:
        argv: Optional command-line arguments (defaults to sys.argv).

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    setup_logging()
    logger.info("Application started")

    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code != 0:
            logger.error("Argument parsing failed")
        return int(exc.code or 0)

    _log_cli_arguments(args)
    print_header()

    try:
        order_input = OrderService.parse_cli_args(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
        logger.info("Input validation passed")
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.message)
        print_error_banner(exc.message)
        return 1

    print_order_summary(order_input)

    if not confirm_proceed():
        print_info("Order cancelled by user.")
        logger.info("Order cancelled by user at confirmation prompt")
        return 0

    try:
        config = BinanceConfig.from_env()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        print_error_banner(str(exc))
        return 1

    try:
        client = BinanceFuturesClient(config)
        order_service = OrderService(client)

        order_service.validate(order_input)

        with execution_timer() as elapsed:
            with spinner("Placing order"):
                result = order_service.place_order(order_input)

        logger.info(
            "Order success | orderId=%s | status=%s | executedQty=%s",
            result.order_id,
            result.status,
            result.executed_qty,
        )
        print_success_banner(result, elapsed[0])
        return 0

    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.message)
        print_error_banner(exc.message)
        return 1

    except BinanceAPIException as exc:
        message = _handle_binance_api_error(exc)
        logger.error("Order failure | %s", message)
        print_error_banner(message)
        return 1

    except BinanceRequestException as exc:
        message = _handle_binance_request_error(exc)
        logger.error("Request failure | %s", message)
        print_error_banner(message)
        return 1

    except ConnectionError:
        message = "Network connection failed. Check your internet connection and try again."
        logger.error(message)
        print_error_banner(message)
        return 1

    except TimeoutError:
        message = "Request timed out. Binance Futures Testnet may be slow or unreachable."
        logger.error(message)
        print_error_banner(message)
        return 1

    except KeyboardInterrupt:
        print()
        print_info("Operation interrupted by user.")
        logger.info("Operation interrupted by user (KeyboardInterrupt)")
        return 130

    except Exception as exc:
        message = f"An unexpected error occurred: {exc}"
        logger.exception("Unexpected error")
        print_error_banner(message)
        return 1


if __name__ == "__main__":
    sys.exit(main())
