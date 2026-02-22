# analyze.py
# Run: python analyze.py

import sqlite3
import pandas as pd
from tabulate import tabulate
from config import DB_PATH, ROUTES

ROUTE_META = {(r["origin"], r["destination"]): r for r in ROUTES}


def sep(title: str):
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


def load_fares() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM fares", conn)
    if df.empty:
        return df
    df["fetched_at"]     = pd.to_datetime(df["fetched_at"])
    df["departure_date"] = pd.to_datetime(df["departure_date"])
    df["region"]         = df.apply(
        lambda r: ROUTE_META.get((r["origin"], r["destination"]), {}).get("region", "Unknown"), axis=1
    )
    return df


# ── 1. Route-level summary ────────────────────────────────────────────────────

def route_summary(df: pd.DataFrame):
    sep("📋  Average Economy Fare by Route & Horizon (USD)")

    g = (
        df.groupby(["region", "origin", "destination", "days_ahead"])["price_total"]
        .agg(avg="mean", min="min", max="max", n="count")
        .round(0).reset_index()
    )

    # Pivot so T+7 / T+30 / T+90 are side-by-side columns
    pivot = g.pivot_table(
        index=["region", "origin", "destination"],
        columns="days_ahead",
        values="avg"
    ).reset_index()
    pivot.columns.name = None

    # Rename horizon columns
    rename = {7: "T+7 avg $", 30: "T+30 avg $", 90: "T+90 avg $"}
    pivot.rename(columns=rename, inplace=True)

    # Add T+7 vs T+30 delta (demand signal)
    if "T+7 avg $" in pivot.columns and "T+30 avg $" in pivot.columns:
        pivot["T+7 vs T+30"] = ((pivot["T+7 avg $"] - pivot["T+30 avg $"])
                                 / pivot["T+30 avg $"] * 100).round(1)
        pivot["T+7 vs T+30"] = pivot["T+7 vs T+30"].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "–"
        )

    pivot = pivot.sort_values(["region", "origin"])
    for col in ["T+7 avg $", "T+30 avg $", "T+90 avg $"]:
        if col in pivot.columns:
            pivot[col] = pivot[col].apply(lambda x: f"${x:.0f}" if pd.notna(x) else "–")

    pivot.columns = [c.replace("origin", "Orig").replace("destination", "Dest")
                      .replace("region", "Region") for c in pivot.columns]
    print(tabulate(pivot, headers="keys", tablefmt="rounded_outline", showindex=False))
    print("\n  T+7 vs T+30: positive = fares rose near departure (strong demand)")
    print("               negative = fares fell near departure (weak demand / discounting)")


# ── 2. Regional average prices ────────────────────────────────────────────────

def regional_prices(df: pd.DataFrame):
    sep("🌍  Average Economy Fare by Region & Horizon (USD)")
    print("  Simple unweighted average across all routes in each region.\n")

    rows = []
    for region in sorted(df["region"].unique()):
        r_df = df[df["region"] == region]
        row  = {"Region": region}
        for h in [7, 30, 90]:
            h_prices = r_df[r_df["days_ahead"] == h]["price_total"]
            row[f"T+{h} avg $"]  = f"${h_prices.mean():.0f}" if not h_prices.empty else "–"
            row[f"T+{h} min $"]  = f"${h_prices.min():.0f}"  if not h_prices.empty else "–"
        row["Routes"] = r_df[["origin", "destination"]].drop_duplicates().shape[0]
        row["Obs"]    = len(r_df)
        rows.append(row)

    print(tabulate(rows, headers="keys", tablefmt="rounded_outline", showindex=False))


# ── 3. Price trend over observation days ──────────────────────────────────────

def price_trend(df: pd.DataFrame):
    sep("📈  Price Trend — How T+30 Fares Changed Over Time")
    print("  Shows whether fares on key routes are rising or falling day-by-day.\n")

    key_routes = [
        ("IST", "LHR", "London"),
        ("IST", "JFK", "New York"),
        ("IST", "NRT", "Tokyo"),
        ("IST", "DXB", "Dubai"),
        ("IST", "GRU", "São Paulo"),
        ("IST", "NBO", "Nairobi"),
    ]

    t30 = df[df["days_ahead"] == 30].copy()
    t30["fetch_date"] = t30["fetched_at"].dt.date

    for orig, dest, name in key_routes:
        subset = t30[(t30["origin"] == orig) & (t30["destination"] == dest)]
        if subset.empty:
            continue
        trend = (
            subset.groupby("fetch_date")["price_total"]
            .agg(avg="mean", min="min").round(0).reset_index()
        )
        trend.columns = ["Date", "Avg $", "Min $"]
        print(f"  {orig}→{dest}  ({name})")
        print(tabulate(trend, headers="keys", tablefmt="simple", showindex=False))
        print()


# ── 4. Fetch log ──────────────────────────────────────────────────────────────

def fetch_log_summary():
    sep("🗂️   Recent Fetch Log (last 20)")
    with sqlite3.connect(DB_PATH) as conn:
        log = pd.read_sql_query(
            "SELECT fetched_at, route, days_ahead, status, n_records, message "
            "FROM fetch_log ORDER BY id DESC LIMIT 20", conn
        )
    print(tabulate(log, headers="keys", tablefmt="rounded_outline", showindex=False))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        df = load_fares()
    except Exception as e:
        print(f"[ERROR] Could not load database: {e}")
        exit(1)

    if df.empty:
        print("No data yet. Run: python fetcher.py")
        fetch_log_summary()
        exit(0)

    print(f"\nLoaded {len(df):,} records | "
          f"{df[['origin','destination']].drop_duplicates().shape[0]} routes | "
          f"{df['fetched_at'].dt.date.nunique()} observation days")

    route_summary(df)
    regional_prices(df)
    price_trend(df)
    fetch_log_summary()
