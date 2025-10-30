# Assignment Trading Bot

A simplified command-line trading bot for the Binance Futures Testnet (USDT-M) built with
Python and the official [`python-binance`](https://github.com/sammchardy/python-binance)
SDK. The bot supports market, limit, and stop-limit orders while providing structured
logging for all API interactions.

## Prerequisites

1. [Register for a Binance Futures Testnet account](https://testnet.binancefuture.com/).
2. Generate API credentials (key and secret) from the Testnet dashboard and activate
   Futures trading permissions.
3. Install Python 3.9 or later.
4. Install project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the CLI script to place orders against the Binance Futures Testnet:

```bash
python main.py \
  --api-key YOUR_API_KEY \
  --api-secret YOUR_API_SECRET \
  --symbol BTCUSDT \
  --side BUY \
  --type LIMIT \
  --quantity 0.001 \
  --price 25000
```

Supported order types:

- `MARKET` – requires `--quantity`.
- `LIMIT` – requires `--quantity` and `--price`.
- `STOP_LIMIT` – requires `--quantity`, `--price`, and `--stop-price`.

Additional options:

- `--time-in-force` – choose from `GTC`, `IOC`, `FOK`, or `GTX` (default: `GTC`).
- `--reduce-only` – mark the order as reduce-only.
- `--log-file` – change the log file path (default: `bot.log`).
- `--log-level` – adjust verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

The CLI validates input values before submitting orders. Responses and errors from the
Binance API are logged and summarized in the console output.

## Logging

Logs are written both to stdout and to the specified log file. Each request includes the
symbol, side, order type, quantity, and optional price parameters. API responses and
errors are recorded to aid in debugging and auditing.

## Notes

- The bot automatically routes requests to `https://testnet.binancefuture.com/fapi` when
  instantiated with `testnet=True`.
- Keep your API credentials secure. Avoid committing them to version control or sharing
  them publicly.
- The provided code focuses on core ordering functionality. Extend the bot with custom
  strategies or additional order types as needed.
