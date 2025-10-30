"""Core trading bot logic for interacting with the Binance Futures Testnet."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

logger = logging.getLogger(__name__)

FUTURES_TESTNET_URL = "https://testnet.binancefuture.com/fapi"


@dataclass
class OrderRequest:
    """Represent the parameters required to place a futures order."""

    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    time_in_force: str = "GTC"
    stop_price: Optional[float] = None
    reduce_only: Optional[bool] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_request_params(self) -> Dict[str, Any]:
        """Convert the order request to python-binance compatible parameters."""
        params: Dict[str, Any] = {
            "symbol": self.symbol.upper(),
            "side": self.side.upper(),
            "type": self.order_type.upper(),
            "quantity": self.quantity,
        }

        if self.price is not None:
            params["price"] = self.price
        if self.order_type.upper() in {"LIMIT", "STOP", "STOP_MARKET", "STOP_LIMIT"}:
            params["timeInForce"] = self.time_in_force
        if self.stop_price is not None:
            params["stopPrice"] = self.stop_price
        if self.reduce_only is not None:
            params["reduceOnly"] = self.reduce_only

        params.update(self.extra_params)
        return params


class BasicBot:
    """Simplified trading bot for Binance Futures Testnet."""

    def __init__(self, api_key: str, api_secret: str, *, testnet: bool = True) -> None:
        self.client = Client(api_key, api_secret, testnet=testnet)
        if testnet:
            # Ensure requests are routed to the Testnet Futures base URL.
            self.client.FUTURES_URL = FUTURES_TESTNET_URL
        self._testnet = testnet
        logger.debug("Initialized BasicBot with testnet=%s", testnet)

    def place_order(self, order: OrderRequest) -> Dict[str, Any]:
        """Place an order using the Binance Futures API."""
        request_params = order.to_request_params()
        logger.info("Sending order request: %s", self._sanitize_for_logging(request_params))
        try:
            response = self.client.futures_create_order(**request_params)
            logger.info("Order response: %s", response)
            return response
        except (BinanceAPIException, BinanceOrderException) as exc:
            logger.error("Binance API error: %s", exc, exc_info=True)
            raise
        except Exception as exc:  # pragma: no cover - unexpected error logging
            logger.exception("Unexpected error when placing order: %s", exc)
            raise

    def place_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: Optional[bool] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convenience method to place a market order."""
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
            reduce_only=reduce_only,
            extra_params=extra_params or {},
        )
        return self.place_order(order)

    def place_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        reduce_only: Optional[bool] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convenience method to place a limit order."""
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            reduce_only=reduce_only,
            extra_params=extra_params or {},
        )
        return self.place_order(order)

    def place_stop_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
        reduce_only: Optional[bool] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Place a stop-limit order, useful for more advanced strategies."""
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type="STOP",
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            reduce_only=reduce_only,
            extra_params={"workingType": "CONTRACT_PRICE", **(extra_params or {})},
        )
        return self.place_order(order)

    @staticmethod
    def _sanitize_for_logging(params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive values before logging."""
        sanitized = dict(params)
        sanitized.pop("signature", None)
        return sanitized
