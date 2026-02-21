"""
Pre-warm the Stock Signal Advisor cache for popular tickers.

Usage:
    python scripts/precache.py
    python scripts/precache.py --url https://xdvpqzqg4m.us-east-2.awsapprunner.com
    python scripts/precache.py --tickers AAPL,MSFT,GOOGL
    python scripts/precache.py --url https://... --tickers AAPL,NVDA --delay 5

The in-memory cache resets on every deployment. Run this script after each
production deploy to ensure the most popular tickers serve instantly.
"""

import argparse
import time
import urllib.request
import urllib.error
import json
import sys

DEFAULT_URL = "http://localhost:8000"
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "VOO", "SPY", "QQQ", "AMD", "META"]
DEFAULT_DELAY = 2  # seconds between requests to avoid overwhelming the service


def analyze_ticker(base_url: str, ticker: str) -> dict | None:
    url = f"{base_url}/api/v1/signal"
    payload = json.dumps({"ticker": ticker}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"  HTTP {e.code}: {body[:120]}")
        return None
    except urllib.error.URLError as e:
        print(f"  Connection error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-warm Stock Signal Advisor cache")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"API base URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated list of tickers to pre-cache",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Seconds between requests (default: {DEFAULT_DELAY})",
    )
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    base_url = args.url.rstrip("/")

    print(f"Pre-warming cache at {base_url}")
    print(f"Tickers: {', '.join(tickers)}\n")

    passed = 0
    failed = 0

    for i, ticker in enumerate(tickers):
        print(f"[{i + 1}/{len(tickers)}] Analyzing {ticker}...", end=" ", flush=True)
        result = analyze_ticker(base_url, ticker)
        if result:
            signal = result.get("signal", "?")
            confidence = result.get("confidence", 0)
            cached = result.get("metadata", {}).get("cached", False)
            status = "cached" if cached else "fresh"
            print(f"{signal} ({confidence:.0%}) [{status}]")
            passed += 1
        else:
            print("FAILED")
            failed += 1

        if i < len(tickers) - 1:
            time.sleep(args.delay)

    print(f"\nDone: {passed} succeeded, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
