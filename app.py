from datetime import timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="BL Search Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    font-size: 18px !important;
}

/* MAIN TITLES */
h1 { font-size: 44px !important; font-weight: 800 !important; }
h2 { font-size: 32px !important; font-weight: 700 !important; }
h3 { font-size: 24px !important; font-weight: 700 !important; }

/* SIDEBAR */
section[data-testid="stSidebar"] {
    width: 380px !important;
    background: #ffffff;
    border-right: 1px solid #eef2f7;
}

section[data-testid="stSidebar"] label {
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* METRIC CARDS */
.metric-card {
    background: white;
    padding: 24px;
    border-radius: 18px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    text-align: center;
    min-height: 200px;
}

.metric-label {
    font-size: 16px;
    color: #6B7280;
    font-weight: 600;
    margin-bottom: 12px;
}

.metric-value {
    font-size: 38px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 12px;
}

.section-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 16px;
    color: #111827;
}

.small-subtitle {
    color: #6b7280;
    font-size: 18px;
    margin-bottom: 20px;
}

</style>
""",
    unsafe_allow_html=True,
)

import io
import requests

# =========================================================
# DATA LOAD & CLEANING
# =========================================================
csv_url = "https://docs.google.com/spreadsheets/d/1z1wOGh4fehBVxDL4JXO1p2p3uZG77sd4FD5jhRXI5qE/gviz/tq?tqx=out:csv&gid=0"


@st.cache_data(ttl=300)
def load_data():
  # Request with standard browser User-Agent to prevent Google 403 HTTP errors
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  response = requests.get(csv_url, headers=headers)
  response.raise_for_status()

  # Load raw text into pandas
  df = pd.read_csv(io.StringIO(response.text))

  # Clean header column names
  df.columns = df.columns.str.strip()

  # Filter out summary/average rows
  df = df[
      ~df["Date"].astype(str).str.lower().isin(["average", "total", "nan", ""])
  ]

  # Parse Date column
  df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
  df = df.dropna(subset=["Date"])

  # Sanitize numeric and percentage columns safely
  for col in df.columns:
    if col != "Date":
      s = (
          df[col]
          .astype(str)
          .str.strip()
          .str.replace(",", "", regex=False)
          .str.replace("$", "", regex=False)
      )
      s = s.str.replace("%", "", regex=False).replace(
          ["None", "#REF!", "#N/A", "#VALUE!", "nan", "None", ""], "0"
      )
      df[col] = pd.to_numeric(s, errors="coerce").fillna(0)

  df = df.sort_values("Date")
  return df


df = load_data()

# =========================================================
# DYNAMIC KPI & COLUMN CATEGORIZATION
# =========================================================
KNOWN_SEARCH_KPIS = [
    "Trade Searches",
    "Seller Searches",
    "Mobile Searches",
    "Android Searches",
    "IOS Searches",
    "Total Searches",
    "Searches excluding top 20 Sellers",
    "Daily Active searchers",
    "Final Zero Result Search",
    "Numeric Searches",
]

KNOWN_TXN_KPIS = [
    "BL Search API Txn",
    "bl search txn",
    "Android",
    "Desktop",
    "iOS",
    "Unique Transactors",
    "Txn from Top 10 position",
    "Bizfeed Txn - BL search page",
    "Numeric Searches Txn",
]

# Auto-discover remaining dynamic sheet columns
existing_cols = [c for c in df.columns if c != "Date"]
uncategorized_cols = [
    c
    for c in existing_cols
    if c not in KNOWN_SEARCH_KPIS and c not in KNOWN_TXN_KPIS
]

SEARCH_KPIS = [c for c in KNOWN_SEARCH_KPIS if c in df.columns]
TXN_KPIS = [c for c in KNOWN_TXN_KPIS if c in df.columns]

for col in uncategorized_cols:
  if any(
      kw in col.lower()
      for kw in ["txn", "transact", "order", "buyer", "seller"]
  ):
    TXN_KPIS.append(col)
  else:
    SEARCH_KPIS.append(col)

# =========================================================
# DERIVED KPIs
# =========================================================
if (
    "BL Search API Txn" in df.columns
    and "Searches excluding top 20 Sellers" in df.columns
):
  df["Txn/100 Searches - removing top 20"] = (
      df["BL Search API Txn"]
      / df["Searches excluding top 20 Sellers"].replace(0, pd.NA)
  ).fillna(0) * 100

if (
    "Txn from Top 10 position" in df.columns
    and "BL Search API Txn" in df.columns
):
  df["Txn from Top 10 position in %"] = (
      df["Txn from Top 10 position"]
      / df["BL Search API Txn"].replace(0, pd.NA)
  ).fillna(0) * 100

if (
    "Final Zero Result Search" in df.columns
    and "Searches excluding top 20 Sellers" in df.columns
):
  df["Zero Search Result % after removing top 20 sellers"] = (
      df["Final Zero Result Search"]
      / df["Searches excluding top 20 Sellers"].replace(0, pd.NA)
  ).fillna(0) * 100

if "Numeric Searches Txn" in df.columns and "Numeric Searches" in df.columns:
  df["Numeric Searches Txn/100 Searches"] = (
      df["Numeric Searches Txn"] / df["Numeric Searches"].replace(0, pd.NA)
  ).fillna(0) * 100

KPI_METRICS = [
    c
    for c in [
        "Txn/100 Searches - removing top 20",
        "Mean Purchase Position - Search",
        "Txn from Top 10 position in %",
        "Zero Search Result % after removing top 20 sellers",
        "Numeric Searches Txn/100 Searches",
    ]
    if c in df.columns
]

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown(
    "<h2 style='font-size:24px;'>Dashboard Filters</h2>", unsafe_allow_html=True
)


def chip_selector(section_name, items, state_key):
  st.sidebar.markdown(f"### {section_name}")

  col_a, col_b = st.sidebar.columns(2)
  if col_a.button("Select All", key=f"all_{state_key}"):
    st.session_state[state_key] = items.copy()
  if col_b.button("Clear All", key=f"clear_{state_key}"):
    st.session_state[state_key] = []

  if state_key not in st.session_state:
    st.session_state[state_key] = []

  cols = st.sidebar.columns(2)
  for idx, item in enumerate(items):
    with cols[idx % 2]:
      checked = st.checkbox(
          item,
          value=item in st.session_state[state_key],
          key=f"{state_key}_{item}",
      )
      if checked and item not in st.session_state[state_key]:
        st.session_state[state_key].append(item)
      elif not checked and item in st.session_state[state_key]:
        st.session_state[state_key].remove(item)


chip_selector("Searches Data", SEARCH_KPIS, "selected_searches")
st.sidebar.markdown("---")
chip_selector("Txn Data", TXN_KPIS, "selected_txns")
st.sidebar.markdown("---")
chip_selector("Derived KPIs", KPI_METRICS, "selected_kpis")

# =========================================================
# HEADER & CONTROL PANEL
# =========================================================
st.title("📊 BL Search Dashboard")
st.markdown(
    "<div class='small-subtitle'>Real-time BL Search KPIs & Automated Google"
    " Sheets Sync</div>",
    unsafe_allow_html=True,
)

with st.container():
  top1, top2 = st.columns(2)
  with top1:
    max_date = (
        df["Date"].max().date() if not df.empty else pd.Timestamp.now().date()
    )
    selected_date = st.date_input("Select Base Comparison Date", value=max_date)
  with top2:
    weeks_compare = st.selectbox("Weeks to Compare", list(range(1, 9)), index=3)

# =========================================================
# DATE COMPARISON LOGIC
# =========================================================
selected_date = pd.to_datetime(selected_date)
comparison_dates = [
    selected_date - timedelta(days=7 * i) for i in range(weeks_compare)
]

comparison_df = df[
    df["Date"].dt.date.isin([d.date() for d in comparison_dates])
].sort_values("Date", ascending=False)

# =========================================================
# EXECUTIVE KPI CARDS
# =========================================================
st.markdown("## Executive KPI Overview")

card_metrics = [
    c
    for c in [
        "Searches excluding top 20 Sellers",
        "Daily Active searchers",
        "Final Zero Result Search",
        "BL Search API Txn",
        "Unique Transactors",
        "Txn/100 Searches - removing top 20",
        "Zero Search Result % after removing top 20 sellers",
        "Numeric Searches Txn/100 Searches",
    ]
    if c in df.columns
]

selected_df = df[df["Date"] == selected_date]
latest = selected_df.iloc[0] if not selected_df.empty else df.iloc[-1]
previous_df = df[df["Date"] < latest["Date"]]
previous = previous_df.iloc[-1] if not previous_df.empty else latest

for i in range(0, len(card_metrics), 4):
  cols = st.columns(4)
  for j in range(4):
    if i + j >= len(card_metrics):
      continue
    metric = card_metrics[i + j]
    current = latest[metric]
    prev = previous[metric]
    delta = current - prev
    delta_pct = (delta / prev * 100) if prev != 0 else 0

    positive = delta >= 0
    badge_color = "#DCFCE7" if positive else "#FEE2E2"
    text_color = "#15803D" if positive else "#DC2626"
    arrow = "↑" if positive else "↓"
    value_str = (
        f"{current:.2f}%"
        if ("%" in metric or "Txn/100" in metric or "Transactor/" in metric)
        else f"{int(current):,}"
    )

    with cols[j]:
      st.markdown(
          f"""
            <div class="metric-card">
                <div class="metric-label">{metric}</div>
                <div class="metric-value">{value_str}</div>
                <span style="background:{badge_color}; color:{text_color}; padding:6px 12px; border-radius:999px; font-size:14px; font-weight:700;">
                    {arrow} {abs(delta_pct):.2f}%
                </span>
            </div>
            """,
          unsafe_allow_html=True,
      )
  st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(
    ["📊 KPI Comparison", "📈 Trend Analysis", "📋 Raw Data"]
)

# =========================================================
# TAB 1: KPI COMPARISON TABLE
# =========================================================
def build_comparison_table(metrics, title):
  st.markdown(
      f"<div class='section-title'>{title}</div>", unsafe_allow_html=True
  )
  if not metrics:
    st.info("Select metrics from the sidebar filter to populate this section.")
    return

  table_df = comparison_df[["Date"] + metrics].copy()
  table_df["Date"] = table_df["Date"].dt.strftime("%Y-%m-%d (%a)")

  st.dataframe(table_df, use_container_width=True, height=350)


with tab1:
  build_comparison_table(
      st.session_state.get("selected_searches", []), "Searches Data"
  )
  st.markdown("---")
  build_comparison_table(
      st.session_state.get("selected_txns", []), "Transactions Data"
  )
  st.markdown("---")
  build_comparison_table(
      st.session_state.get("selected_kpis", []), "Derived KPIs"
  )

# =========================================================
# TAB 2: TREND ANALYSIS
# =========================================================
with tab2:
  st.markdown(
      "<div class='section-title'>Trend Visualizations</div>",
      unsafe_allow_html=True,
  )

  col_t1, col_t2 = st.columns([2, 1])
  with col_t1:
    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_range = st.slider(
        "Select Date Range for Trends",
        min_value=min_d,
        max_value=max_d,
        value=(min_d, max_d),
    )
  with col_t2:
    chart_type = st.radio(
        "Chart Style", ["Line Chart", "Bar Chart"], horizontal=True
    )

  filtered_trend_df = df[
      (df["Date"].dt.date >= date_range[0])
      & (df["Date"].dt.date <= date_range[1])
  ]

  def render_chart(metrics, title):
    st.subheader(title)
    if not metrics:
      st.info("Select metrics from sidebar to display chart.")
      return

    fig = go.Figure()
    for metric in metrics:
      if metric in filtered_trend_df.columns:
        if chart_type == "Line Chart":
          fig.add_trace(
              go.Scatter(
                  x=filtered_trend_df["Date"],
                  y=filtered_trend_df[metric],
                  mode="lines+markers",
                  name=metric,
              )
          )
        else:
          fig.add_trace(
              go.Bar(
                  x=filtered_trend_df["Date"],
                  y=filtered_trend_df[metric],
                  name=metric,
              )
          )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

  render_chart(
      st.session_state.get("selected_searches", []), "Search Trends"
  )
  render_chart(
      st.session_state.get("selected_txns", []), "Transaction Trends"
  )
  render_chart(st.session_state.get("selected_kpis", []), "KPI Trends")

# =========================================================
# TAB 3: RAW DATA & SEARCH
# =========================================================
with tab3:
  st.markdown(
      "<div class='section-title'>Raw Sheet Data</div>", unsafe_allow_html=True
  )
  search_text = st.text_input("Search raw dataset by keyword...")

  raw_df = df.copy()
  if search_text:
    raw_df = raw_df[
        raw_df.astype(str)
        .apply(lambda x: x.str.contains(search_text, case=False))
        .any(axis=1)
    ]

  st.download_button(
      "⬇ Download Filtered CSV",
      data=raw_df.to_csv(index=False),
      file_name="bl_search_raw_data.csv",
      mime="text/csv",
  )
  st.dataframe(raw_df, use_container_width=True, height=600)