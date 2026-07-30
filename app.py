from datetime import timedelta
import io
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="BL Search Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CUSTOM CSS FOR SCREENSHOT-EXACT PILL CHIP UI & FONTS
# =========================================================
st.markdown(
    """
<style>
/* GLOBAL FONT ENHANCEMENT */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 19px !important;
}

/* CONTAINER CARDS */
.main-card {
    background-color: #ffffff;
    padding: 24px 30px;
    border-radius: 18px;
    border: 1px solid #e2e8f0;
    box-shadow: 0px 4px 16px rgba(15, 23, 42, 0.04);
    margin-bottom: 24px;
}

/* HEADINGS */
h1 { font-size: 42px !important; font-weight: 800 !important; color: #0f172a !important; margin-bottom: 20px !important; }
h2 { font-size: 32px !important; font-weight: 800 !important; color: #0f172a !important; }

/* LABEL FONTS */
.stDateInput label, .stSelectbox label, .stTextInput label {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #334155 !important;
}

/* PILL CHIP STYLING FOR BUTTONS */
div[data-testid="column"] button {
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 17px !important;
    padding: 8px 22px !important;
    height: 44px !important;
    margin-bottom: 10px !important;
    transition: all 0.2s ease-in-out !important;
}

/* ACTIVE SELECTED CHIP BUTTONS */
.chip-active button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: 1.5px solid #2563eb !important;
    box-shadow: 0px 4px 10px rgba(37, 99, 235, 0.25) !important;
}

/* INACTIVE CHIP BUTTONS */
.chip-inactive button {
    background-color: #ffffff !important;
    color: #334155 !important;
    border: 1.5px solid #cbd5e1 !important;
}

.chip-inactive button:hover {
    background-color: #f1f5f9 !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
}

/* EXPANDER TITLE FONTS */
.stExpander details summary p {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #334155 !important;
}

/* DATAFRAME & TABLE STYLING */
[data-testid="stDataFrame"] {
    font-size: 19px !important;
}

/* TAB FONT ENHANCEMENTS */
button[data-baseweb="tab"] div {
    font-size: 22px !important;
    font-weight: 700 !important;
}

</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# DATA LOAD & CLEANING
# =========================================================
csv_url = "https://docs.google.com/spreadsheets/d/1z1wOGh4fehBVxDL4JXO1p2p3uZG77sd4FD5jhRXI5qE/gviz/tq?tqx=out:csv&gid=0"


@st.cache_data(ttl=300)
def load_data():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  response = requests.get(csv_url, headers=headers)
  response.raise_for_status()

  df = pd.read_csv(io.StringIO(response.text))
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
          ["None", "#REF!", "#N/A", "#VALUE!", "nan", ""], "0"
      )
      df[col] = pd.to_numeric(s, errors="coerce").fillna(0)

  df = df.sort_values("Date")
  return df


df = load_data()

# =========================================================
# KPI CATEGORY & DEFAULT DEFINITIONS
# =========================================================
KPI_GROUPS = {
    "Main KPIs": {
        "metrics": [
            "Txn/100 Searches - removing top 20",
            "Mean Purchase Position - Search",
            "Txn from Top 10 position in %",
            "Zero Search Result % after removing top 20 sellers",
            "Transactor/Searcher",
            "ABL TXN/Total",
            "NI/TXN",
        ],
        "defaults": [
            "Txn/100 Searches - removing top 20",
            "Zero Search Result % after removing top 20 sellers",
            "Transactor/Searcher",
            "NI/TXN",
        ],
    },
    "Searches": {
        "metrics": [
            "Total Searches",
            "Daily Active searchers",
            "Searches by top 20",
            "Other touch point searches",
            "Searches excluding top 20 Sellers",
            "Zero Result Searches",
            "Zero Result by top 20 sellers",
            "Final Zero Result Search",
        ],
        "defaults": ["Total Searches", "Searches excluding top 20 Sellers"],
    },
    "Platform wise searches": {
        "metrics": [
            "Trade Searches",
            "Seller Searches",
            "Mobile Searches",
            "Android Searches",
            "IOS Searches",
            "Trade Searchers",
            "Seller Searchers",
            "Mobile Searchers",
            "Android Searchers",
            "IOS Searchers",
        ],
        "defaults": [],
    },
    "Transaction Overall & Platform Wise": {
        "metrics": [
            "bl search txn",
            "Unique Transactors",
            "Android",
            "Desktop",
            "iOS",
            "imob",
            "Andorid transactor",
            "desktop transactor",
            "ios tranactor",
            "imob transactor",
            "ABL Txn",
            "Txn from Top 10 position",
            "Bizfeed Txn - BL search page",
        ],
        "defaults": ["bl search txn"],
    },
    "Transaction DLP wise": {
        "metrics": [
            "Global Txn",
            "Global Txr",
            "All India Txn",
            "All India Txr",
            "Foriegn Txn",
            "Foriegn Txr",
            "Local Txn",
            "Local Txr",
            "Hyper Local Txn",
            "Hyper Local Txr",
        ],
        "defaults": [],
    },
    "Transaction GRID Wise": {
        "metrics": [
            "H/L NR Txn",
            "H/L NR Txn ABL",
            "H/L R Txn",
            "H/L R Txn ABL",
            "I/G NR Txn",
            "I/G NR Txn ABL",
            "I/G R Txn",
            "I/G R Txn ABL",
            "Foriegn GRID Txn",
            "Foriegn GRID Txn ABL",
        ],
        "defaults": [],
    },
    "Search NI": {
        "metrics": [
            "Search NI",
            "Search NI Users",
            "NI ABL",
            "Search NI top 5",
            "Search NI top 10",
        ],
        "defaults": ["Search NI"],
    },
    "Reason wise NI": {
        "metrics": [
            "wrong category",
            "specification mismatch",
            "wrong location",
            "insufficient information",
            "retail leads",
            "brand issue",
            "other",
            "wrong search result",
        ],
        "defaults": [],
    },
    "DLP Wise NI": {
        "metrics": [
            "Global NI",
            "Global NI User",
            "All India NI",
            "All India NI User",
            "Foriegn NI",
            "Foriegn NI User",
            "Local NI",
            "Local NI User",
            "HyperLocal NI",
            "HyperLocal NI User",
        ],
        "defaults": [],
    },
    "Device Wise NI": {
        "metrics": [
            "Desktop NI",
            "Deskop NI user",
            "Android NI",
            "Android NI User",
            "IOS NI",
            "IOS NI User",
            "Mobile NI",
            "Mobile NI User",
        ],
        "defaults": [],
    },
    "Grid Wise NI": {
        "metrics": [
            "H/L NR NI",
            "H/L NR NI ABL",
            "H/L R NI",
            "H/L R NI ABL",
            "I/G NR NI",
            "I/G NR NI ABL",
            "I/G R NI",
            "I/G R NI ABL",
            "Foriegn GRID NI",
            "Foriegn GRID NI ABL",
        ],
        "defaults": [],
    },
}

# Derived KPIs
if (
    "BL Search API Txn" in df.columns
    and "Searches excluding top 20 Sellers" in df.columns
):
  df["Txn/100 Searches - removing top 20"] = (
      df["BL Search API Txn"]
      / df["Searches excluding top 20 Sellers"].replace(0, pd.NA)
  ).fillna(0) * 100

if (
    "Final Zero Result Search" in df.columns
    and "Searches excluding top 20 Sellers" in df.columns
):
  df["Zero Search Result % after removing top 20 sellers"] = (
      df["Final Zero Result Search"]
      / df["Searches excluding top 20 Sellers"].replace(0, pd.NA)
  ).fillna(0) * 100

# Initialize Session State
for cat, data in KPI_GROUPS.items():
  key = f"selected_{cat}"
  if key not in st.session_state:
    st.session_state[key] = [d for d in data["defaults"] if d in df.columns]

# =========================================================
# DASHBOARD HEADER
# =========================================================
st.title("📊 BL Search Dashboard")

# =========================================================
# TOP ROW CONTROLS (SCREENSHOT TOP CARD)
# =========================================================
with st.container():
  st.markdown("<div class='main-card'>", unsafe_allow_html=True)

  c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])

  with c1:
    max_date = (
        df["Date"].max().date() if not df.empty else pd.Timestamp.now().date()
    )
    selected_date = st.date_input("Select Date", value=max_date)

  with c2:
    weeks_compare = st.selectbox(
        "Weeks to Compare", ["1 Week", "2 Weeks", "3 Weeks", "4 Weeks", "5 Weeks", "6 Weeks", "7 Weeks", "8 Weeks"], index=3
    )
    weeks_num = int(weeks_compare.split()[0])

  with c3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Exclude days", key="btn_ex_days", use_container_width=True)

  with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Exclude dates", key="btn_ex_dates", use_container_width=True)

  st.markdown("</div>", unsafe_allow_html=True)

selected_date = pd.to_datetime(selected_date)
comparison_dates = [
    selected_date - timedelta(days=7 * i) for i in range(weeks_num)
]
comparison_df = df[
    df["Date"].dt.date.isin([d.date() for d in comparison_dates])
].sort_values("Date", ascending=False)

# =========================================================
# KPI SELECTION PANEL WITH REAL PILL CHIPS
# =========================================================
with st.container():
  st.markdown("<div class='main-card'>", unsafe_allow_html=True)

  # Inline header row matching screenshot
  hdr_col1, hdr_col2, hdr_col3, hdr_col4 = st.columns([1.2, 2.5, 1, 1])

  with hdr_col1:
    st.markdown(
        "<h3 style='margin:0; padding-top:4px;'>Select KPIs</h3>",
        unsafe_allow_html=True,
    )

  with hdr_col2:
    search_query = st.text_input(
        "Search KPIs",
        placeholder="🔍 Search KPIs...",
        label_visibility="collapsed",
    ).strip().lower()

  with hdr_col3:
    if st.button("✕ Deselect All", key="deselect_all_top", use_container_width=True):
      for cat in KPI_GROUPS.keys():
        st.session_state[f"selected_{cat}"] = []
      st.rerun()

  with hdr_col4:
    if st.button("🔄 Reset", key="reset_top", use_container_width=True):
      for cat, data in KPI_GROUPS.items():
        st.session_state[f"selected_{cat}"] = [
            d for d in data["defaults"] if d in df.columns
        ]
      st.rerun()

  st.markdown("<br>", unsafe_allow_html=True)

  # Render Collapsible Expander Categories
  for cat, data in KPI_GROUPS.items():
    available_metrics = [m for m in data["metrics"] if m in df.columns]

    if search_query:
      available_metrics = [
          m for m in available_metrics if search_query in m.lower()
      ]
      if not available_metrics:
        continue

    selected_list = st.session_state[f"selected_{cat}"]
    sel_count = len(selected_list)
    is_expanded = bool(search_query or cat in ["Main KPIs", "Searches"])

    expander_title = f"{'—' if is_expanded else '+'} {cat.upper()} ({sel_count} selected)"

    with st.expander(expander_title, expanded=is_expanded):
      if not available_metrics:
        st.caption("No matching KPIs found.")
      else:
        # Render Pill Chips in flexible rows
        # Divide metrics into columns for balanced pill layout
        cols_per_row = 4
        num_metrics = len(available_metrics)

        for i in range(0, num_metrics, cols_per_row):
          chip_cols = st.columns(cols_per_row)
          for j in range(cols_per_row):
            if i + j < num_metrics:
              metric_name = available_metrics[i + j]
              is_selected = metric_name in selected_list

              with chip_cols[j]:
                # Wrap button in CSS class for active/inactive styling
                wrapper_class = "chip-active" if is_selected else "chip-inactive"
                st.markdown(f"<div class='{wrapper_class}'>", unsafe_allow_html=True)

                btn_label = f"✓ {metric_name}" if is_selected else metric_name
                if st.button(
                    btn_label, key=f"pill_{cat}_{metric_name}", use_container_width=True
                ):
                  if is_selected:
                    st.session_state[f"selected_{cat}"].remove(metric_name)
                  else:
                    st.session_state[f"selected_{cat}"].append(metric_name)
                  st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

  st.markdown("</div>", unsafe_allow_html=True)

# Gather all active selected KPIs
active_selected_kpis = []
for cat in KPI_GROUPS.keys():
  for metric in st.session_state[f"selected_{cat}"]:
    if metric not in active_selected_kpis:
      active_selected_kpis.append(metric)

# =========================================================
# DASHBOARD TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(
    ["📊 KPI Comparison", "📈 Trend Analysis", "📋 Raw Data"]
)

# =========================================================
# TAB 1: KPI COMPARISON TABLE
# =========================================================
with tab1:
  st.markdown("## KPI Comparison Table")

  if not active_selected_kpis:
    st.info("💡 Please click on KPI pill chips above to select metrics.")
  else:
    table_df = comparison_df[["Date"] + active_selected_kpis].copy()
    table_df["Date"] = table_df["Date"].dt.strftime("%Y-%m-%d (%a)")

    st.download_button(
        "⬇ Export Table CSV",
        data=table_df.to_csv(index=False),
        file_name="kpi_comparison.csv",
        mime="text/csv",
    )

    st.dataframe(table_df, use_container_width=True, height=520)

# =========================================================
# TAB 2: TREND ANALYSIS
# =========================================================
with tab2:
  st.markdown("## Trend Visualizations")

  if not active_selected_kpis:
    st.info("💡 Select KPI chips above to display visual trends.")
  else:
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

    fig = go.Figure()
    for metric in active_selected_kpis:
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
        height=550,
        font=dict(size=18),
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 3: RAW DATA & SEARCH
# =========================================================
with tab3:
  st.markdown("## Raw Sheet Data")
  search_text = st.text_input("Search raw dataset by keyword...")

  raw_df = df.copy()
  if search_text:
    raw_df = raw_df[
        raw_df.astype(str)
        .apply(lambda x: x.str.contains(search_text, case=False))
        .any(axis=1)
    ]

  st.download_button(
      "⬇ Download Full Raw CSV",
      data=raw_df.to_csv(index=False),
      file_name="bl_search_raw_data.csv",
      mime="text/csv",
  )
  st.dataframe(raw_df, use_container_width=True, height=600)