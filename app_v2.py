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
    page_title="BL Search Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CUSTOM CSS MATCHING SCREENSHOT UI
# =========================================================
st.markdown(
    """
<style>
/* GLOBAL FONTS */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 19px !important;
    background-color: #f8fafc;
}

/* CONTAINER CARDS */
.main-card {
    background-color: #ffffff;
    padding: 24px 30px;
    border-radius: 18px;
    border: 1px solid #e2e8f0;
    box-shadow: 0px 4px 16px rgba(15, 23, 42, 0.03);
    margin-bottom: 24px;
}

/* SECTION HEADINGS */
.row-header {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #0284c7 !important;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* PILL CHIP BUTTONS */
div[data-testid="column"] button {
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 17px !important;
    padding: 6px 20px !important;
    height: 44px !important;
    margin-bottom: 8px !important;
    transition: all 0.2s ease-in-out !important;
}

/* SELECTED CHIP (CORAL RED STYLE MATCHING SCREENSHOT) */
.chip-active button {
    background-color: #fef2f2 !important;
    color: #ef4444 !important;
    border: 1.5px solid #ef4444 !important;
    box-shadow: 0px 2px 6px rgba(239, 68, 68, 0.15) !important;
}

/* UNSELECTED CHIP */
.chip-inactive button {
    background-color: #ffffff !important;
    color: #334155 !important;
    border: 1.5px solid #e2e8f0 !important;
}

.chip-inactive button:hover {
    background-color: #f8fafc !important;
    border-color: #cbd5e1 !important;
    color: #0f172a !important;
}

/* DATAFRAME / TABLE STYLING */
[data-testid="stDataFrame"] {
    font-size: 20px !important;
}

thead tr th {
    font-size: 21px !important;
    font-weight: 800 !important;
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
}

tbody tr td {
    font-size: 19px !important;
    padding: 12px !important;
}

/* TABS STYLING */
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
# KPI CATEGORIES WITH ICONS & DEFAULTS
# =========================================================
KPI_GROUPS = {
    "Main KPIs": {
        "icon": "🌐",
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
        "icon": "📊",
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
        "icon": "🛒",
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
        "icon": "🎯",
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
        "icon": "⭐",
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
        "icon": "📈",
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
        "icon": "🔍",
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
        "icon": "📋",
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
        "icon": "📍",
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
        "icon": "📱",
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
        "icon": "🔷",
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

# Initialize Session State Defaults
for cat, data in KPI_GROUPS.items():
  key = f"selected_{cat}"
  if key not in st.session_state:
    st.session_state[key] = [d for d in data["defaults"] if d in df.columns]

# =========================================================
# DASHBOARD TITLE
# =========================================================
st.title("⚡ BL Search Analytics")

# =========================================================
# TOP CONTROLS ROW
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
        "Weeks to Compare",
        [
            "1 Week",
            "2 Weeks",
            "3 Weeks",
            "4 Weeks",
            "5 Weeks",
            "6 Weeks",
            "7 Weeks",
            "8 Weeks",
        ],
        index=3,
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
# KPI SELECTION PANEL (ROW-BASED PILL CHIPS LIKE SCREENSHOT)
# =========================================================
with st.container():
  st.markdown("<div class='main-card'>", unsafe_allow_html=True)

  # Header Actions
  hdr1, hdr2, hdr3, hdr4 = st.columns([1.2, 2.5, 1, 1])

  with hdr1:
    st.markdown(
        "<h3 style='margin:0; padding-top:4px;'>Select KPIs</h3>",
        unsafe_allow_html=True,
    )

  with hdr2:
    search_query = st.text_input(
        "Search KPIs",
        placeholder="🔍 Search KPIs...",
        label_visibility="collapsed",
    ).strip().lower()

  with hdr3:
    if st.button("✕ Deselect All", key="deselect_all_top", use_container_width=True):
      for cat in KPI_GROUPS.keys():
        st.session_state[f"selected_{cat}"] = []
      st.rerun()

  with hdr4:
    if st.button("🔄 Reset", key="reset_top", use_container_width=True):
      for cat, data in KPI_GROUPS.items():
        st.session_state[f"selected_{cat}"] = [
            d for d in data["defaults"] if d in df.columns
        ]
      st.rerun()

  st.markdown("<hr style='margin: 16px 0 24px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)

  # Render Row-by-Row Categories Matching Screenshot Layout
  for cat, data in KPI_GROUPS.items():
    available_metrics = [m for m in data["metrics"] if m in df.columns]

    if search_query:
      available_metrics = [
          m for m in available_metrics if search_query in m.lower()
      ]
      if not available_metrics:
        continue

    selected_list = st.session_state[f"selected_{cat}"]

    # Divide row into Title (left), Pill Chips (middle), More Switch (right)
    col_label, col_chips, col_more = st.columns([2.2, 7, 1])

    with col_label:
      st.markdown(
          f"<div class='row-header'><span>{data['icon']}</span> {cat}</div>",
          unsafe_allow_html=True,
      )

    # Determine default visible limit (first 5 chips shown by default)
    show_more_key = f"more_{cat}"
    if show_more_key not in st.session_state:
      st.session_state[show_more_key] = False

    limit = len(available_metrics) if st.session_state[show_more_key] else 5
    visible_metrics = available_metrics[:limit]

    with col_chips:
      # Horizontal layout for chips
      cols_per_row = 5
      for idx in range(0, len(visible_metrics), cols_per_row):
        chip_cols = st.columns(cols_per_row)
        batch = visible_metrics[idx : idx + cols_per_row]
        for c_idx, metric_name in enumerate(batch):
          is_selected = metric_name in selected_list
          with chip_cols[c_idx]:
            wrapper_class = "chip-active" if is_selected else "chip-inactive"
            st.markdown(f"<div class='{wrapper_class}'>", unsafe_allow_html=True)

            if st.button(
                metric_name, key=f"pill_{cat}_{metric_name}", use_container_width=True
            ):
              if is_selected:
                st.session_state[f"selected_{cat}"].remove(metric_name)
              else:
                st.session_state[f"selected_{cat}"].append(metric_name)
              st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    with col_more:
      if len(available_metrics) > 5:
        is_toggled = st.toggle("More", value=st.session_state[show_more_key], key=f"toggle_{cat}")
        if is_toggled != st.session_state[show_more_key]:
          st.session_state[show_more_key] = is_toggled
          st.rerun()

    st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

  st.markdown("</div>", unsafe_allow_html=True)

# Active Selected KPIs Collection
active_selected_kpis = []
for cat in KPI_GROUPS.keys():
  for metric in st.session_state[f"selected_{cat}"]:
    if metric not in active_selected_kpis:
      active_selected_kpis.append(metric)

# =========================================================
# DASHBOARD TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(
    ["📊 KPI Comparison Table", "📈 Trend Visualizations", "📋 Raw Sheet Data"]
)

# =========================================================
# TAB 1: KPI COMPARISON TABLE
# =========================================================
with tab1:
  st.markdown("## KPI Comparison Table")

  if not active_selected_kpis:
    st.info("💡 Please click on KPI chips above to display analytics.")
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
# TAB 3: RAW DATA
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