"""Command-line interface for interacting with the Binance Futures trading bot."""
from __future__ import annotations

import argparse
import logging
import sys
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict

from binance.exceptions import BinanceAPIException, BinanceOrderException

from bot import BasicBot


def configure_logging(log_file: str, log_level: str) -> None:
    """Configure logging handlers for console and file output."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger()
    if logger.handlers:
        # Avoid duplicate handlers if configure_logging is called multiple times.
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class PositiveDecimal(argparse.Action):
    """Argparse action to validate positive decimal inputs."""

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: str, option_string: str | None = None) -> None:  # noqa: D401,E501
        value = self._parse_positive_decimal(parser, values, option_string)
        setattr(namespace, self.dest, float(value))

    @staticmethod
    def _parse_positive_decimal(
        parser: argparse.ArgumentParser, values: str, option_string: str | None
    ) -> Decimal:
        try:
            value = Decimal(values)
        except InvalidOperation as exc:  # pragma: no cover - argparse formatting
            parser.error(f"Invalid decimal value for {option_string or ''}: {values}")
            raise exc
        if value <= 0:
            parser.error(f"{option_string or ''} must be greater than 0")
        return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place orders on the Binance Futures Testnet using python-binance."
    )
    parser.add_argument("--api-key", required=True, help="Binance API key")
    parser.add_argument("--api-secret", required=True, help="Binance API secret")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair symbol (e.g., BTCUSDT)")
    parser.add_argument(
        "--side",
        choices=["BUY", "SELL"],
        required=True,
        help="Order side",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        default="MARKET",
        help="Order type to execute",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        action=PositiveDecimal,
        help="Order quantity (base asset amount)",
    )
    parser.add_argument(
        "--price",
        action=PositiveDecimal,
        help="Limit price for LIMIT or STOP_LIMIT orders",
    )
    parser.add_argument(
        "--stop-price",
        dest="stop_price",
        action=PositiveDecimal,
        help="Stop price for STOP_LIMIT orders",
    )
    parser.add_argument(
        "--time-in-force",
        default="GTC",
        choices=["GTC", "IOC", "FOK", "GTX"],
        help="Time in force for limit-based orders",
    )
    parser.add_argument(
        "--reduce-only",
        action="store_true",
        help="Mark order as reduce-only",
    )
    parser.add_argument(
        "--log-file",
        default="bot.log",
        help="Path to the log file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser


def execute_order(args: argparse.Namespace, bot: BasicBot) -> Dict[str, Any]:
    order_dispatch: Dict[str, Callable[..., Dict[str, Any]]] = {
        "MARKET": bot.place_market_order,
        "LIMIT": bot.place_limit_order,
        "STOP_LIMIT": bot.place_stop_limit_order,
    }

    kwargs: Dict[str, Any] = {
        "symbol": args.symbol,
        "side": args.side,
        "quantity": args.quantity,
    }

    if args.reduce_only:
        kwargs["reduce_only"] = True

    if args.order_type == "LIMIT":
        if args.price is None:
            raise ValueError("--price is required for LIMIT orders")
        kwargs.update({"price": args.price, "time_in_force": args.time_in_force})
    elif args.order_type == "STOP_LIMIT":
        if args.price is None or args.stop_price is None:
            raise ValueError("--price and --stop-price are required for STOP_LIMIT orders")
        kwargs.update(
            {
                "price": args.price,
                "stop_price": args.stop_price,
                "time_in_force": args.time_in_force,
            }
        )

    logging.getLogger(__name__).debug("Dispatching %s order with kwargs=%s", args.order_type, kwargs)
    return order_dispatch[args.order_type](**kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_file, args.log_level)

    bot = BasicBot(args.api_key, args.api_secret, testnet=True)

    try:
        response = execute_order(args, bot)
    except (BinanceAPIException, BinanceOrderException) as exc:
        logging.error("Binance error: %s", exc)
        print("Order failed:", exc)
        return 1
    except ValueError as exc:
        logging.error("Input validation error: %s", exc)
        print("Input error:", exc)
        return 2
    except Exception as exc:  # pragma: no cover - unexpected error
        logging.exception("Unexpected error")
        print("Unexpected error:", exc)
        return 3

    print("Order placed successfully!")
    print("Symbol:", response.get("symbol"))
    print("Order ID:", response.get("orderId"))
    print("Status:", response.get("status"))
    print("Type:", response.get("type"))
    print("Side:", response.get("side"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
