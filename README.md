# ✈️ TK Fare Tracker

Track Turkish Airlines ticket prices daily for IST→Tokyo routes to build RASK insights.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API credentials
```bash
cp .env .env
# Edit .env and paste your Amadeus API Key and Secret
```

Get your keys at: https://developers.amadeus.com → My Self-Service Workspace → Create New App

### 3. Run a one-off fetch (test it works)
```bash
python fetcher.py
```

### 4. Start the daily scheduler
```bash
python scheduler.py
```
This runs a fetch immediately on startup, then every day at 08:00.
Leave it running in a terminal or use `nohup` / `screen` to keep it alive.

```bash
# Run in background with nohup
nohup python scheduler.py > logs/scheduler.log 2>&1 &
```

### 5. Analyze collected data
```bash
python analyze.py
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `config.py` | Routes, horizons, cabin classes |
| `fetcher.py` | Amadeus API calls + data parsing |
| `database.py` | SQLite read/write |
| `scheduler.py` | Daily job runner |
| `analyze.py` | Summaries + RASK yield proxy |
| `fares.db` | Auto-created SQLite database |
| `.env` | Your API credentials (never commit this) |

---

## Understanding the Data

### Schema: `fares` table
| Column | Description |
|--------|-------------|
| `fetched_at` | UTC timestamp of when we queried |
| `departure_date` | The future date we searched |
| `days_ahead` | 30 or 90 — how far ahead from fetch date |
| `cabin` | ECONOMY or BUSINESS |
| `airline` | Carrier code (TK = Turkish Airlines) |
| `price_total` | Total fare in USD |
| `price_base` | Base fare (excl. taxes) |
| `duration` | Flight duration (ISO 8601, e.g. PT14H30M) |
| `stops` | 0 = direct, 1+ = connecting |

### RASK Proxy Methodology
```
Yield ($/km) = Average Fare / Great Circle Distance
RASK estimate = Yield × Published Load Factor
```
Turkish Airlines publishes monthly load factors in their investor relations traffic reports:
https://investor.turkishairlines.com/en/financial-operational-data/operational-statistics

---

## Notes on Test vs Production API
- **Test environment**: Returns cached/simulated data (not real prices). Good for development.
- **Production environment**: Real live prices. Request access via Amadeus dashboard after validating your app.

Change `AMADEUS_ENV=production` in `.env` when ready.

---

## Extending the Project
- Add more routes in `config.py` → `ROUTES` list
- Add a Streamlit dashboard: `pip install streamlit` and query `fares.db`
- Export to Excel: `df.to_excel("fares_export.xlsx")` in `analyze.py`
- Add return leg: include `returnDate` in the Amadeus API call
