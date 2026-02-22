# dashboard.py — TK Fare Tracker Dashboard
# Run: streamlit run dashboard.py

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from config import DB_PATH, ROUTES

st.set_page_config(page_title="TK Fare Tracker", page_icon="✈️", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

  html, body, [class*="css"] {
      font-family: 'IBM Plex Sans', sans-serif;
      background-color: #0d0d0d;
      color: #e8e8e8;
  }
  .block-container { padding: 2rem 2.5rem; }
  .tk-header { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 0.25rem; }
  .tk-title  { font-family: 'IBM Plex Mono', monospace; font-size: 2rem; font-weight: 600; color: #e8230a; letter-spacing: -0.5px; }
  .tk-sub    { font-size: 0.85rem; color: #666; font-family: 'IBM Plex Mono', monospace; }

  .kpi-row { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
  .kpi-card {
      background: #161616; border: 1px solid #2a2a2a;
      border-left: 3px solid #e8230a; padding: 1rem 1.25rem;
      flex: 1; min-width: 140px;
  }
  .kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.3rem; }
  .kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 600; color: #f0f0f0; }
  .kpi-delta { font-size: 0.75rem; margin-top: 0.2rem; }
  .up   { color: #e8230a; }
  .down { color: #22c55e; }

  .section-title {
      font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem;
      text-transform: uppercase; letter-spacing: 2px; color: #555;
      border-bottom: 1px solid #222; padding-bottom: 0.4rem; margin: 2rem 0 1rem;
  }
  #MainMenu, footer, header { visibility: hidden; }
  .stSelectbox label, .stMultiSelect label { color: #888; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

ROUTE_META = {(r["origin"], r["destination"]): r for r in ROUTES}
REGIONS    = sorted({r["region"] for r in ROUTES})

@st.cache_data(ttl=300)
def load_data():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df  = pd.read_sql_query("SELECT * FROM fares", conn)
            log = pd.read_sql_query("SELECT * FROM fetch_log ORDER BY id DESC LIMIT 100", conn)
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

    if df.empty:
        return df, log

    df["fetched_at"]     = pd.to_datetime(df["fetched_at"])
    df["departure_date"] = pd.to_datetime(df["departure_date"])
    df["fetch_date"]     = pd.to_datetime(df["fetched_at"].dt.date)
    df["region"]         = df.apply(
        lambda r: ROUTE_META.get((r["origin"], r["destination"]), {}).get("region", "Unknown"), axis=1
    )
    df["route"] = df["origin"] + "→" + df["destination"]
    return df, log

PLOTLY_THEME = dict(
    paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d",
    font_color="#aaa", font_family="IBM Plex Mono",
    yaxis=dict(gridcolor="#1f1f1f", linecolor="#333"),
)

# Distinct colors per region
REGION_COLORS = {
    "Far East":      "#e8230a",
    "Europe":        "#ff6b4a",
    "North America": "#ffa94d",
    "Middle East":   "#ffe066",
    "Africa":        "#69db7c",
    "Latin America": "#4dabf7",
    "Domestic":      "#cc5de8",
}

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="tk-header">
  <span class="tk-title">✈ TK FARE TRACKER</span>
  <span class="tk-sub">Economy · IST departures · USD</span>
</div>
""", unsafe_allow_html=True)

df, log = load_data()

if df.empty:
    st.warning("No data yet. Run `python fetcher.py` to collect fares.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────

last_fetch   = df["fetched_at"].max()
n_routes     = df["route"].nunique()
n_obs_days   = df["fetch_date"].nunique()
avg_t7       = df[df["days_ahead"] == 7]["price_total"].mean()
avg_t30      = df[df["days_ahead"] == 30]["price_total"].mean()
avg_t90      = df[df["days_ahead"] == 90]["price_total"].mean()
demand_delta = ((avg_t7 - avg_t30) / avg_t30 * 100) if avg_t30 else 0
demand_label = "🟢 Strong" if demand_delta > 3 else "🔴 Weak" if demand_delta < -3 else "🟡 Neutral"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Last Fetch</div>
    <div class="kpi-value" style="font-size:1rem">{last_fetch.strftime('%b %d %H:%M')}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Routes Tracked</div>
    <div class="kpi-value">{n_routes}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Observation Days</div>
    <div class="kpi-value">{n_obs_days}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg T+7 Fare</div>
    <div class="kpi-value">${avg_t7:,.0f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg T+30 Fare</div>
    <div class="kpi-value">${avg_t30:,.0f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg T+90 Fare</div>
    <div class="kpi-value">${avg_t90:,.0f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Network Demand</div>
    <div class="kpi-value" style="font-size:1rem">{demand_label}</div>
    <div class="kpi-delta {'up' if demand_delta > 0 else 'down'}">{demand_delta:+.1f}% T+7 vs T+30</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📈 Price Trends", "🌍 Regional Snapshot", "🗂️ Fetch Log"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Price Trends (main tab)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Controls ──────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        sel_horizon = st.selectbox(
            "Horizon", [7, 30, 90], index=1,
            format_func=lambda x: f"T+{x} ({x} days out)"
        )
    with c2:
        sel_region = st.selectbox("Region", ["All regions"] + REGIONS)
    with c3:
        # Route options filtered by region
        if sel_region == "All regions":
            route_pool = sorted(df["route"].unique())
        else:
            route_pool = sorted(df[df["region"] == sel_region]["route"].unique())

        default_routes = route_pool[:4]
        sel_routes = st.multiselect("Routes (optional — leave empty to show region avg)", route_pool, default=default_routes)

    st.markdown('<div class="section-title">Average Fare Over Time</div>', unsafe_allow_html=True)

    horizon_df = df[df["days_ahead"] == sel_horizon].copy()

    # ── Chart A: per-route lines (if routes selected) ─────────────────────────
    if sel_routes:
        plot_df = horizon_df[horizon_df["route"].isin(sel_routes)]
        daily   = (
            plot_df.groupby(["fetch_date", "route", "region"])["price_total"]
            .mean().reset_index()
        )
        daily.columns = ["Date", "Route", "Region", "Avg Fare $"]

        if daily.empty:
            st.info(f"No T+{sel_horizon} data yet for selected routes.")
        else:
            # Color by region
            color_map = {r: REGION_COLORS.get(daily[daily["Route"]==r]["Region"].iloc[0], "#aaa")
                         for r in daily["Route"].unique()}

            fig = go.Figure()
            for route in daily["Route"].unique():
                sub = daily[daily["Route"] == route]
                fig.add_trace(go.Scatter(
                    x=sub["Date"], y=sub["Avg Fare $"],
                    name=route,
                    mode="lines+markers",
                    line=dict(color=color_map.get(route, "#aaa"), width=2),
                    marker=dict(size=6),
                    hovertemplate="%{y:$,.0f}<extra>" + route + "</extra>",
                ))
            fig.update_layout(
                **PLOTLY_THEME, height=420,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.08, font_size=11),
                yaxis_title="Avg Fare (USD)",
                xaxis_title="Observation Date",
            )
            fig.update_xaxes(type="date", tickformat="%b %d", gridcolor="#1f1f1f", linecolor="#333")
            st.plotly_chart(fig, use_container_width=True)

    # ── Chart B: region average lines ─────────────────────────────────────────
    st.markdown('<div class="section-title">Regional Average Fare Over Time</div>', unsafe_allow_html=True)

    region_filter = horizon_df if sel_region == "All regions" else horizon_df[horizon_df["region"] == sel_region]
    region_daily  = (
        region_filter.groupby(["fetch_date", "region"])["price_total"]
        .mean().reset_index()
    )
    region_daily.columns = ["Date", "Region", "Avg Fare $"]

    if region_daily.empty:
        st.info(f"No T+{sel_horizon} data yet.")
    else:
        fig_reg = go.Figure()
        for region in sorted(region_daily["Region"].unique()):
            sub = region_daily[region_daily["Region"] == region]
            fig_reg.add_trace(go.Scatter(
                x=sub["Date"], y=sub["Avg Fare $"],
                name=region,
                mode="lines+markers",
                line=dict(color=REGION_COLORS.get(region, "#aaa"), width=2.5),
                marker=dict(size=7),
                hovertemplate="%{y:$,.0f}<extra>" + region + "</extra>",
            ))
        fig_reg.update_layout(
            **PLOTLY_THEME, height=400,
            hovermode="x unified",
            legend=dict(orientation="h", y=1.08, font_size=11),
            yaxis_title="Avg Fare (USD)",
            xaxis_title="Observation Date",
        )
        fig_reg.update_xaxes(type="date", tickformat="%b %d", gridcolor="#1f1f1f", linecolor="#333")
        st.plotly_chart(fig_reg, use_container_width=True)

    # ── Chart C: horizon comparison for latest day ─────────────────────────────
    st.markdown('<div class="section-title">Latest Snapshot — T+7 / T+30 / T+90 by Region</div>', unsafe_allow_html=True)

    latest_date = df["fetch_date"].max()
    latest_df   = df[df["fetch_date"] == latest_date]
    if sel_region != "All regions":
        latest_df = latest_df[latest_df["region"] == sel_region]

    latest_agg = (
        latest_df.groupby(["region", "days_ahead"])["price_total"]
        .mean().reset_index()
    )
    latest_agg["Horizon"] = latest_agg["days_ahead"].apply(lambda x: f"T+{x}")

    if not latest_agg.empty:
        fig_snap = px.bar(
            latest_agg, x="region", y="price_total", color="Horizon",
            barmode="group",
            labels={"price_total": "Avg Fare $", "region": "Region"},
            color_discrete_map={"T+7": "#e8230a", "T+30": "#ff9a7a", "T+90": "#3a3a3a"},
        )
        fig_snap.update_layout(
            **PLOTLY_THEME, height=360,
            legend=dict(orientation="h", y=1.08),
            xaxis_title="", yaxis_title="Avg Fare (USD)",
        )
        fig_snap.update_traces(marker_line_width=0)
        st.plotly_chart(fig_snap, use_container_width=True)
        st.caption(f"As of {latest_date}. Each bar group shows T+7/T+30/T+90 fares side-by-side for the same region.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Regional Snapshot
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    # Region summary table
    st.markdown('<div class="section-title">Average Fare by Region & Horizon</div>', unsafe_allow_html=True)

    rows = []
    for region in REGIONS:
        r_df = df[df["region"] == region]
        row  = {"Region": region}
        for h in [7, 30, 90]:
            prices = r_df[r_df["days_ahead"] == h]["price_total"]
            row[f"T+{h}"]     = prices.mean() if not prices.empty else None
            row[f"T+{h} min"] = prices.min()  if not prices.empty else None
        if row.get("T+7") and row.get("T+30"):
            delta = (row["T+7"] - row["T+30"]) / row["T+30"] * 100
            row["Δ T+7/T+30"] = f"{delta:+.1f}%"
            row["_delta"]      = delta
        else:
            row["Δ T+7/T+30"] = "–"
            row["_delta"]      = 0
        row["Routes"] = r_df["route"].nunique()
        rows.append(row)

    region_df = pd.DataFrame(rows)

    display_df = region_df[["Region", "T+7", "T+30", "T+90", "Δ T+7/T+30", "Routes"]].copy()
    for col in ["T+7", "T+30", "T+90"]:
        display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "–")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Demand signal bar
    st.markdown('<div class="section-title">Demand Signal — T+7 vs T+30 (% difference)</div>', unsafe_allow_html=True)
    sig = region_df[["Region", "_delta"]].dropna().sort_values("_delta")
    colors = ["#22c55e" if x > 3 else "#e8230a" if x < -3 else "#888" for x in sig["_delta"]]
    fig_sig = go.Figure(go.Bar(
        x=sig["_delta"], y=sig["Region"], orientation="h",
        marker_color=colors,
        text=[f"{x:+.1f}%" for x in sig["_delta"]],
        textposition="outside",
    ))
    fig_sig.update_layout(
        **PLOTLY_THEME, height=320,
        xaxis_title="T+7 vs T+30 (%)",
        xaxis_zeroline=True, xaxis_zerolinecolor="#444",
        showlegend=False,
    )
    st.plotly_chart(fig_sig, use_container_width=True)
    st.caption("Green = T+7 > T+30 (fares rise near departure = seats filling). Red = T+7 < T+30 (discounting last-minute = weak demand).")

    # Per-region route breakdown
    st.markdown('<div class="section-title">Route Detail by Region</div>', unsafe_allow_html=True)
    sel_detail_region = st.selectbox("Select region", REGIONS, key="detail_region")

    detail_df = df[df["region"] == sel_detail_region]
    route_rows = []
    for route in sorted(detail_df["route"].unique()):
        r = detail_df[detail_df["route"] == route]
        row = {"Route": route}
        for h in [7, 30, 90]:
            prices = r[r["days_ahead"] == h]["price_total"]
            row[f"T+{h} avg"] = prices.mean() if not prices.empty else None
            row[f"T+{h} min"] = prices.min()  if not prices.empty else None
        if row.get("T+7 avg") and row.get("T+30 avg"):
            delta = (row["T+7 avg"] - row["T+30 avg"]) / row["T+30 avg"] * 100
            row["Demand"] = "🟢 Strong" if delta > 3 else "🔴 Weak" if delta < -3 else "🟡 Neutral"
            row["Δ%"]     = f"{delta:+.1f}%"
        else:
            row["Demand"] = "–"
            row["Δ%"]     = "–"
        route_rows.append(row)

    rdf = pd.DataFrame(route_rows)
    for col in ["T+7 avg", "T+30 avg", "T+90 avg", "T+7 min", "T+30 min", "T+90 min"]:
        if col in rdf.columns:
            rdf[col] = rdf[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "–")
    st.dataframe(rdf, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Fetch Log
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Fetch History</div>', unsafe_allow_html=True)
    if log.empty:
        st.info("No fetch log found.")
    else:
        success = log[log["status"] == "success"]
        errors  = log[log["status"] == "error"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Total fetches", len(log))
        m2.metric("Successful",    len(success))
        m3.metric("Errors",        len(errors))
        st.dataframe(log, use_container_width=True, hide_index=True)