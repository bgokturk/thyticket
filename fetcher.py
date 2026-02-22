# fetcher.py
#
# DATA SOURCE: fast-flights (free, no API key)
# FX RATES:    Yahoo Finance via yfinance (free, live)
# ─────────────────────────────────────────────────────
# Setup:
#   pip install fast-flights playwright yfinance
#   playwright install

import json
import re
import time
from datetime import datetime, timedelta

import yfinance as yf
from fast_flights import FlightData, Passengers, get_flights
from config import ROUTES, SEARCH_HORIZONS, MAX_RESULTS
from database import save_fares, log_fetch, init_db

REQUEST_DELAY = 2  # seconds between calls

# ── Live FX rates ─────────────────────────────────────────────────────────────
#
# Yahoo Finance FX ticker convention:
#   "USDTRY=X"  → how many TRY per 1 USD  (~36.5)  ← this is what yf returns for "TRY=X"
#   "TRYUSD=X"  → how many USD per 1 TRY  (~0.027) ← what we actually want
#
# To avoid confusion we always fetch the USD-per-foreign-currency rate directly
# using the XXXUSD=X format, which gives us the multiplier we need:
#   price_usd = price_local * rate
#
# Fallbacks in case Yahoo Finance is unreachable:
FALLBACK_RATES = {
    "TRY": 0.0274,   # 1 TRY = ~0.027 USD
    "EUR": 1.08,
    "GBP": 1.27,
    "USD": 1.0,
}

CURRENCIES_NEEDED = ["TRY", "EUR", "GBP"]


def fetch_fx_rates() -> dict:
    """
    Fetch live X-to-USD rates from Yahoo Finance.
    Uses XXXUSD=X tickers (e.g. TRYUSD=X) which return USD per 1 unit of XXX.
    Returns dict like {"TRY": 0.0274, "EUR": 1.081, "USD": 1.0}
    """
    rates = {"USD": 1.0}
    # TRYUSD=X means "price of 1 TRY in USD" — exactly what we want
    tickers = [f"{c}USD=X" for c in CURRENCIES_NEEDED]

    try:
        data = yf.download(tickers, period="1d", interval="1d",
                           progress=False, auto_adjust=True)
        closes = data["Close"].iloc[-1]

        for currency in CURRENCIES_NEEDED:
            ticker = f"{currency}USD=X"
            try:
                rate = float(closes[ticker])
                if rate <= 0:
                    raise ValueError("Non-positive rate")
                rates[currency] = rate
                print(f"  [FX] 1 {currency} = {rate:.5f} USD (live)")
            except Exception:
                rates[currency] = FALLBACK_RATES[currency]
                print(f"  [FX] 1 {currency} = {FALLBACK_RATES[currency]:.5f} USD (fallback)")

    except Exception as e:
        print(f"  [FX] Yahoo Finance error: {e} — using fallback rates")
        rates.update(FALLBACK_RATES)

    return rates


# ── Price parsing ─────────────────────────────────────────────────────────────

def parse_currency(price_str: str) -> str:
    """Extract currency code from strings like 'TRY 32,351' or '$850'."""
    s = price_str.strip()
    if s.startswith("$"):
        return "USD"
    match = re.match(r"([A-Z]{3})", s)
    return match.group(1) if match else "USD"


def parse_price_usd(price_str: str, fx_rates: dict) -> float:
    """
    Parse a price string and convert to USD.
    'TRY\xa032,351'  →  strip non-numerics  →  32351  →  × 0.0274  →  $886
    '$1,250'         →  1250  × 1.0  →  $1250
    """
    currency = parse_currency(price_str)
    numeric  = re.sub(r"[^\d.,]", "", price_str).replace(",", "")
    amount   = float(numeric)
    rate     = fx_rates.get(currency, 1.0)
    return round(amount * rate, 2)


# ── Core fetch ────────────────────────────────────────────────────────────────

def fetch_fares(origin: str, destination: str, departure_date: str,
                days_ahead: int, fx_rates: dict) -> int:
    fetched_at = datetime.utcnow().isoformat()
    route_key  = f"{origin}-{destination}"

    for fetch_mode in ["local", "fallback"]:
        try:
            result = get_flights(
                flight_data=[
                    FlightData(
                        date=departure_date,
                        from_airport=origin,
                        to_airport=destination,
                    )
                ],
                trip="one-way",
                seat="economy",
                passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
                fetch_mode=fetch_mode,
            )

            if not result or not result.flights:
                print(f"  [{fetch_mode}] No flights returned, trying next mode...")
                continue

            records = []
            for flight in result.flights[:MAX_RESULTS]:
                price_raw = getattr(flight, "price", None)
                if price_raw is None:
                    continue
                try:
                    price_usd = parse_price_usd(str(price_raw), fx_rates)
                except (ValueError, AttributeError) as e:
                    print(f"  [WARN] Could not parse price '{price_raw}': {e}")
                    continue

                records.append({
                    "fetched_at":     fetched_at,
                    "origin":         origin,
                    "destination":    destination,
                    "departure_date": departure_date,
                    "days_ahead":     days_ahead,
                    "airline":        getattr(flight, "name", ""),
                    "price_total":    price_usd,
                    "price_base":     price_usd,
                    "currency":       "USD",
                    "duration":       str(getattr(flight, "duration", "")),
                    "stops":          getattr(flight, "stops", 0),
                    "raw_offer":      json.dumps({
                        "name":      getattr(flight, "name", ""),
                        "price_raw": str(price_raw),
                        "price_usd": price_usd,
                        "departure": str(getattr(flight, "departure", "")),
                        "arrival":   str(getattr(flight, "arrival", "")),
                        "duration":  str(getattr(flight, "duration", "")),
                        "stops":     getattr(flight, "stops", 0),
                        "is_best":   getattr(flight, "is_best", False),
                    }),
                })

            if not records:
                print(f"  [{fetch_mode}] No parseable prices, trying next mode...")
                continue

            save_fares(records)
            log_fetch(route_key, days_ahead, "success", len(records), f"mode={fetch_mode}")
            print(f"  → {len(records)} offers saved [mode={fetch_mode}]")
            return len(records)

        except Exception as e:
            print(f"  [{fetch_mode}] Error: {e}")
            continue

    log_fetch(route_key, days_ahead, "error", 0, "All modes failed")
    print(f"  → Skipped — all modes failed.")
    return 0


# ── Main ──────────────────────────────────────────────────────────────────────

def fetch_all():
    init_db()
    today       = datetime.today()
    total_saved = 0

    print("\nFetching live FX rates from Yahoo Finance...")
    fx_rates = fetch_fx_rates()

    print(f"\nRoutes: {len(ROUTES)} | Horizons: {SEARCH_HORIZONS}")
    print(f"Total calls: {len(ROUTES) * len(SEARCH_HORIZONS)}\n")

    for route in ROUTES:
        origin      = route["origin"]
        destination = route["destination"]
        label       = route["label"]

        for days_ahead in SEARCH_HORIZONS:
            departure_date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            print(f"[FETCH] {label} | T+{days_ahead} ({departure_date})")
            n = fetch_fares(origin, destination, departure_date, days_ahead, fx_rates)
            total_saved += n
            time.sleep(REQUEST_DELAY)

    print(f"\n✅ Done. Total records saved: {total_saved}")


if __name__ == "__main__":
    fetch_all()