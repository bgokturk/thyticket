# config.py

ROUTES = [

    # ── UZAK DOĞU (Far East) ──────────────────────────────────────────
    {"origin": "IST", "destination": "NRT", "label": "IST→Tokyo Narita",    "region": "Far East",      "distance_km": 8968},
    {"origin": "IST", "destination": "HND", "label": "IST→Tokyo Haneda",    "region": "Far East",      "distance_km": 9015},
    {"origin": "IST", "destination": "ICN", "label": "IST→Seoul Incheon",   "region": "Far East",      "distance_km": 8437},
    {"origin": "IST", "destination": "PVG", "label": "IST→Shanghai Pudong", "region": "Far East",      "distance_km": 7773},

    # ── AVRUPA (Europe) ───────────────────────────────────────────────
    {"origin": "IST", "destination": "LHR", "label": "IST→London Heathrow", "region": "Europe",        "distance_km": 2510},
    {"origin": "IST", "destination": "CDG", "label": "IST→Paris CDG",       "region": "Europe",        "distance_km": 2245},
    {"origin": "IST", "destination": "FRA", "label": "IST→Frankfurt",        "region": "Europe",        "distance_km": 2190},
    {"origin": "IST", "destination": "AMS", "label": "IST→Amsterdam",        "region": "Europe",        "distance_km": 2210},

    # ── K. AMERİKA (North America) ────────────────────────────────────
    {"origin": "IST", "destination": "JFK", "label": "IST→New York JFK",    "region": "North America", "distance_km": 9380},
    {"origin": "IST", "destination": "ORD", "label": "IST→Chicago O'Hare",  "region": "North America", "distance_km": 9440},
    {"origin": "IST", "destination": "LAX", "label": "IST→Los Angeles",      "region": "North America", "distance_km": 10680},

    # ── ORTA DOĞU (Middle East) ───────────────────────────────────────
    {"origin": "IST", "destination": "DXB", "label": "IST→Dubai",           "region": "Middle East",   "distance_km": 2580},
    {"origin": "IST", "destination": "DOH", "label": "IST→Doha",            "region": "Middle East",   "distance_km": 2560},
    {"origin": "IST", "destination": "RUH", "label": "IST→Riyadh",          "region": "Middle East",   "distance_km": 2240},

    # ── AFRİKA (Africa) ───────────────────────────────────────────────
    {"origin": "IST", "destination": "CAI", "label": "IST→Cairo",           "region": "Africa",        "distance_km": 1200},
    {"origin": "IST", "destination": "NBO", "label": "IST→Nairobi",         "region": "Africa",        "distance_km": 4280},
    {"origin": "IST", "destination": "LOS", "label": "IST→Lagos",           "region": "Africa",        "distance_km": 4670},

    # ── O. & G. AMERİKA (Latin America) ──────────────────────────────
    {"origin": "IST", "destination": "GRU", "label": "IST→São Paulo",       "region": "Latin America", "distance_km": 10395},
    {"origin": "IST", "destination": "EZE", "label": "IST→Buenos Aires",    "region": "Latin America", "distance_km": 11575},
    {"origin": "IST", "destination": "SCL", "label": "IST→Santiago",        "region": "Latin America", "distance_km": 12020},

    # ── İÇ HATLAR (Domestic) ──────────────────────────────────────────
    {"origin": "IST", "destination": "ESB", "label": "IST→Ankara",          "region": "Domestic",      "distance_km": 350},
    {"origin": "IST", "destination": "ADB", "label": "IST→Izmir",           "region": "Domestic",      "distance_km": 445},
    {"origin": "IST", "destination": "AYT", "label": "IST→Antalya",         "region": "Domestic",      "distance_km": 510},
]

# Days ahead from today to search — these are fixed moving windows, not pinned dates
SEARCH_HORIZONS = [7, 30, 90]

# Economy only
CABIN_CLASSES = ["ECONOMY"]

# Max results per Amadeus API call
MAX_RESULTS = 10

# SQLite database file
DB_PATH = "fares.db"
