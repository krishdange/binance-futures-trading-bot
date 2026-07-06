"""CLI utilities: formatting, banners, spinner, and timers."""

import itertools
import sys
import threading
import time
from contextlib import contextmanager
from decimal import Decimal
from typing import Generator

from colorama import Fore, Style, init
from tabulate import tabulate

from bot.orders import OrderResult
from bot.validators import OrderInput

init(autoreset=True)

BANNER_WIDTH = 41
SPINNER_FRAMES = ("|", "/", "-", "\\")


def print_header(title: str = "Trading Bot") -> None:
    """Print the application header banner."""
    line = "=" * BANNER_WIDTH
    print()
    print(f"{Fore.CYAN}{Style.BRIGHT}{line}")
    print(f"{title:^{BANNER_WIDTH}}")
    print(f"{line}{Style.RESET_ALL}")
    print()


def print_order_summary(order_input: OrderInput) -> None:
    """
    Display a formatted order summary table.

    Args:
        order_input: Validated order parameters.
    """
    price_display = (
        _format_display_decimal(order_input.price)
        if order_input.price is not None
        else f"{Fore.YELLOW}MARKET PRICE{Style.RESET_ALL}"
    )

    side_color = Fore.GREEN if order_input.side == "BUY" else Fore.RED

    table_data = [
        ["Symbol", f"{Fore.WHITE}{Style.BRIGHT}{order_input.symbol}{Style.RESET_ALL}"],
        ["Side", f"{side_color}{Style.BRIGHT}{order_input.side}{Style.RESET_ALL}"],
        ["Type", f"{Fore.MAGENTA}{order_input.order_type}{Style.RESET_ALL}"],
        ["Quantity", f"{Fore.WHITE}{_format_display_decimal(order_input.quantity)}{Style.RESET_ALL}"],
        ["Price", price_display],
    ]

    print(f"{Fore.CYAN}{Style.BRIGHT}Order Summary{Style.RESET_ALL}")
    print()
    print(tabulate(table_data, tablefmt="plain"))
    print()
    print(f"{Fore.CYAN}{'=' * BANNER_WIDTH}{Style.RESET_ALL}")
    print()


def print_success_banner(result: OrderResult, elapsed_seconds: float) -> None:
    """
    Display a success banner with order execution details.

    Args:
        result: Order execution result.
        elapsed_seconds: Time taken to place the order.
    """
    line = "=" * BANNER_WIDTH
    print()
    print(f"{Fore.GREEN}{Style.BRIGHT}{line}")
    print(f"{'SUCCESS':^{BANNER_WIDTH}}")
    print(f"{line}{Style.RESET_ALL}")
    print()

    details = [
        ["Order ID", f"{Fore.GREEN}{result.order_id}{Style.RESET_ALL}"],
        ["Status", f"{Fore.GREEN}{result.status}{Style.RESET_ALL}"],
        ["Executed Qty", result.executed_qty],
        ["Average Price", result.avg_price],
        ["Timestamp", result.timestamp],
        ["Execution Time", f"{elapsed_seconds:.2f}s"],
    ]

    print(tabulate(details, tablefmt="plain"))
    print()
    print(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
    print()


def print_error_banner(message: str) -> None:
    """
    Display a formatted error banner.

    Args:
        message: User-friendly error message.
    """
    line = "=" * BANNER_WIDTH
    print()
    print(f"{Fore.RED}{Style.BRIGHT}{line}")
    print(f"{'ERROR':^{BANNER_WIDTH}}")
    print(f"{line}{Style.RESET_ALL}")
    print()
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")
    print()
    print(f"{Fore.RED}{line}{Style.RESET_ALL}")
    print()


def print_info(message: str) -> None:
    """Print an informational message."""
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")


def confirm_proceed() -> bool:
    """
    Prompt the user to confirm order placement.

    Returns:
        True if the user confirms, False otherwise.
    """
    while True:
        try:
            response = input(f"{Fore.CYAN}Proceed? (y/n): {Style.RESET_ALL}").strip().lower()
        except EOFError:
            return False

        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False

        print_info("Please enter 'y' or 'n'.")


class Spinner:
    """Animated terminal spinner for long-running operations."""

    def __init__(self, message: str = "Placing order") -> None:
        self._message = message
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the spinner in a background thread."""
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def _spin(self) -> None:
        """Run the spinner animation loop."""
        for frame in itertools.cycle(SPINNER_FRAMES):
            if self._stop_event.is_set():
                break
            sys.stdout.write(f"\r{Fore.CYAN}{frame} {self._message}...{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.1)


@contextmanager
def spinner(message: str = "Placing order") -> Generator[None, None, None]:
    """
    Context manager that shows a spinner while work is in progress.

    Args:
        message: Spinner message to display.

    Yields:
        None
    """
    spin = Spinner(message)
    spin.start()
    try:
        yield
    finally:
        spin.stop()


@contextmanager
def execution_timer() -> Generator[list[float], None, None]:
    """
    Context manager that tracks execution elapsed time.

    Yields:
        A list containing the elapsed time in seconds (updated on exit).
    """
    elapsed: list[float] = [0.0]
    start = time.perf_counter()
    try:
        yield elapsed
    finally:
        elapsed[0] = time.perf_counter() - start


def _format_display_decimal(value: Decimal) -> str:
    """Format a Decimal for display."""
    return format(value.normalize(), "f")
