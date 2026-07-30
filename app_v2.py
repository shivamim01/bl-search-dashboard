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
    page_title="BL Search RCA DashBoard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CUSTOM CSS FOR MATCHING TABLE & CHIP UI
# =========================================================
st.markdown(
    """
<style>
/* GLOBAL FONTS - COMPACT & READABLE */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 15px !important;
    background-color: #f8fafc;
}

/* CONTAINER CARDS */
.main-card {
    background-color: #ffffff;
    padding: 16px 20px;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0px 3px 12px rgba(15, 23, 42, 0.03);
    margin-bottom: 16px;
}

/* SECTION HEADINGS */
.row-header {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #0284c7 !important;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* CUSTOM STYLING FOR NATIVE STREAMLIT PILLS */
div[data-testid="stPills"] button {
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 999px !important;
    padding: 3px 12px !important;
}

div[data-testid="stPills"] button[aria-selected="true"] {
    background-color: #fef2f2 !important;
    color: #ef4444 !important;
    border: 1.5px solid #ef4444 !important;
    font-weight: 700 !important;
}

/* DYNAMIC TABLE HTML STYLING */
.custom-table-container {
    width: 100%;
    overflow-x: auto;
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 3px 10px rgba(0,0,0,0.03);
    margin-top: 12px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
    text-align: center;
    font-size: 14px;
}

.custom-table th {
    background-color: #f8fafc;
    color: #475569;
    font-weight: 700;
    padding: 12px 10px;
    border-bottom: 1.5px solid #e2e8f0;
    border-right: 1px solid #f1f5f9;
    font-size: 13.5px !important;
}

.custom-table td {
    padding: 10px 8px;
    border-bottom: 1px solid #f1f5f9;
    border-right: 1px solid #f1f5f9;
    color: #1e293b;
    vertical-align: middle;
    font-size: 13px !important;
}

.custom-table tr:hover {
    background-color: #f8fafc;
}

/* PERCENTAGE BADGES */
.badge-pos {
    color: #10b981;
    font-weight: 700;
    font-size: 12px;
    margin-left: 4px;
}

.badge-neg {
    color: #ef4444;
    font-weight: 700;
    font-size: 12px;
    margin-left: 4px;
}

.badge-neutral {
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
    margin-left: 4px;
}

.sub-avg-pos {
    display: block;
    font-size: 11px;
    color: #10b981;
    font-weight: 600;
    margin-top: 2px;
}

.sub-avg-neg {
    display: block;
    font-size: 11px;
    color: #ef4444;
    font-weight: 600;
    margin-top: 2px;
}

/* SUMMARY ROWS */
.avg-row {
    background-color: #ffffff;
    font-weight: 700;
    color: #0f172a;
}

.best-row {
    background-color: #ffffff;
    font-weight: 800;
    color: #0284c7;
}

/* MODE SELECTION SEGMENTED CONTROL TABS */
div[data-testid="stSegmentedControl"] button {
    font-size: 15px !important;
    font-weight: 700 !important;
    padding: 8px 24px !important;
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

if "custom_kpis_dict" not in st.session_state:
  st.session_state["custom_kpis_dict"] = {}

if "excluded_days" not in st.session_state:
  st.session_state["excluded_days"] = []

if "excluded_dates" not in st.session_state:
  st.session_state["excluded_dates"] = []

if "dr_quick_filter" not in st.session_state:
  st.session_state["dr_quick_filter"] = "Past Week"


def reset_to_strict_defaults():
  for cat, data in KPI_GROUPS.items():
    defaults = [d for d in data["defaults"] if d in df.columns]
    st.session_state[f"selected_{cat}"] = defaults
    st.session_state[f"pills_{cat}"] = defaults
  st.session_state["custom_kpis_dict"] = {}


# Apply Custom Calculated Fields directly onto df
for c_name, c_info in st.session_state["custom_kpis_dict"].items():
  a_col, op, b_col = c_info["a"], c_info["op"], c_info["b"]
  if a_col in df.columns and b_col in df.columns:
    if op == "÷ (Ratio A/B)":
      df[c_name] = (df[a_col] / df[b_col].replace(0, pd.NA)).fillna(0) * 100
    elif op == "× (Multiply A*B)":
      df[c_name] = df[a_col] * df[b_col]
    elif op == "+ (Add A+B)":
      df[c_name] = df[a_col] + df[b_col]
    elif op == "- (Subtract A-B)":
      df[c_name] = df[a_col] - df[b_col]

all_kpi_options = []
for cat, data in KPI_GROUPS.items():
  for m in data["metrics"]:
    if m in df.columns and m not in all_kpi_options:
      all_kpi_options.append(m)

# =========================================================
# DASHBOARD TITLE
# =========================================================
st.title("⚡ BL Search RCA DashBoard")

max_data_date = (
    df["Date"].max().date() if not df.empty else pd.Timestamp.now().date()
)


def render_exclusion_popovers(key_prefix: str):
  c3, c4 = st.columns([1, 1])
  with c3:
    day_count = len(st.session_state["excluded_days"])
    pop_days_label = (
        f"Exclude Days ({day_count})" if day_count > 0 else "Exclude Days"
    )
    with st.popover(pop_days_label, use_container_width=True):
      st.caption("Select days of the week to exclude from analysis:")
      days_list = [
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
          "Saturday",
          "Sunday",
      ]
      sel_days = st.multiselect(
          "Select Days",
          days_list,
          default=st.session_state["excluded_days"],
          key=f"{key_prefix}_pop_sel_days",
      )
      if sel_days != st.session_state["excluded_days"]:
        st.session_state["excluded_days"] = sel_days
        st.rerun()

  with c4:
    date_count = len(st.session_state["excluded_dates"])
    pop_dates_label = (
        f"Exclude Dates ({date_count})" if date_count > 0 else "Exclude Dates"
    )
    with st.popover(pop_dates_label, use_container_width=True):
      st.caption("Select specific dates to exclude:")
      sel_dates = st.date_input(
          "Select Dates",
          value=st.session_state["excluded_dates"],
          key=f"{key_prefix}_pop_sel_dates",
      )
      if isinstance(sel_dates, (list, tuple)):
        st.session_state["excluded_dates"] = list(sel_dates)
      elif sel_dates:
        st.session_state["excluded_dates"] = [sel_dates]


# =========================================================
# TOP LEVEL MODE SELECTION SWITCH
# =========================================================
selected_mode = st.segmented_control(
    "Comparison Mode",
    options=[
        "Previous Week Same Day",
        "Date Range Comparison",
        "Week on Week Comparison",
        "Custom Compare",
    ],
    default="Previous Week Same Day",
    key="top_comparison_mode_switcher",
    label_visibility="collapsed",
)

active_mode_df = pd.DataFrame()
mode_view_type = "pwsd"

# 1. MODE: PREVIOUS WEEK SAME DAY
if selected_mode == "Previous Week Same Day":
  with st.container():
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    c1, c2, c3_4 = st.columns([1.5, 1.5, 2.4])

    with c1:
      selected_date = st.date_input(
          "Select Date", value=max_data_date, key="pwsd_date"
      )

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
          key="pwsd_weeks",
      )
      weeks_num = int(weeks_compare.split()[0])

    with c3_4:
      st.markdown("<br>", unsafe_allow_html=True)
      render_exclusion_popovers(key_prefix="pwsd")

    st.markdown("</div>", unsafe_allow_html=True)

  s_date = pd.to_datetime(selected_date)
  comp_dates = [s_date - timedelta(days=7 * i) for i in range(weeks_num)]
  active_mode_df = df[
      df["Date"].dt.date.isin([d.date() for d in comp_dates])
  ].sort_values("Date", ascending=False)
  mode_view_type = "pwsd"

# 2. MODE: DATE RANGE COMPARISON
elif selected_mode == "Date Range Comparison":
  with st.container():
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    dc1, dc2 = st.columns([2.5, 3])

    with dc1:
      q_val = st.session_state["dr_quick_filter"]
      days_back = (
          7
          if q_val == "Past Week"
          else (
              14
              if q_val == "2 Weeks"
              else (21 if q_val == "3 Weeks" else 28)
          )
      )
      default_start = max_data_date - timedelta(days=days_back)

      selected_dr = st.date_input(
          "Date Range",
          value=(default_start, max_data_date),
          key="dr_picker",
      )

    with dc2:
      st.markdown("**Quick Filters**")
      q_cols = st.columns(4)
      for idx, q_label in enumerate(
          ["Past Week", "2 Weeks", "3 Weeks", "4 Weeks"]
      ):
        with q_cols[idx]:
          if st.button(
              q_label,
              key=f"qf_btn_{q_label}",
              use_container_width=True,
          ):
            st.session_state["dr_quick_filter"] = q_label
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    render_exclusion_popovers(key_prefix="dr")
    st.markdown("</div>", unsafe_allow_html=True)

  if isinstance(selected_dr, (list, tuple)) and len(selected_dr) == 2:
    start_d, end_d = selected_dr[0], selected_dr[1]
  else:
    start_d, end_d = (
        selected_dr,
        selected_dr if not isinstance(selected_dr, (list, tuple)) else max_data_date,
    )

  active_mode_df = df[
      (df["Date"].dt.date >= start_d) & (df["Date"].dt.date <= end_d)
  ].sort_values("Date", ascending=True)
  mode_view_type = "date_range"

# 3. MODE: WEEK ON WEEK COMPARISON
elif selected_mode == "Week on Week Comparison":
  with st.container():
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown("### Week on Week Comparison")
    st.caption(
        "Showing the latest completed Sunday to Saturday weeks, aggregated"
        " by weekly averages."
    )

    wc1, wc2 = st.columns([1.5, 3.5])
    with wc1:
      wow_weeks = st.selectbox(
          "Weeks to compare",
          ["2 Weeks", "3 Weeks", "4 Weeks", "5 Weeks", "6 Weeks", "8 Weeks"],
          index=2,
          key="wow_weeks_sel",
      )
      wow_num = int(wow_weeks.split()[0])

    st.markdown("</div>", unsafe_allow_html=True)

  df_wow = df.copy()
  df_wow["Week_Start"] = df_wow["Date"].apply(
      lambda d: d - timedelta(days=(d.weekday() + 1) % 7)
  )

  numeric_cols = [c for c in df_wow.columns if c not in ["Date", "Week_Start"]]
  weekly_avg_df = (
      df_wow.groupby("Week_Start")[numeric_cols].mean().reset_index()
  )
  weekly_avg_df = weekly_avg_df.rename(columns={"Week_Start": "Date"})

  active_mode_df = weekly_avg_df.sort_values(
      "Date", ascending=False
  ).head(wow_num).sort_values("Date", ascending=True)
  mode_view_type = "wow"

# 4. MODE: CUSTOM COMPARE
else:
  st.info("💡 Select custom dates or dimensions for tailored comparisons.")
  mode_view_type = "custom"


# APPLY GLOBAL DAY AND DATE EXCLUSIONS
if st.session_state["excluded_days"] and not active_mode_df.empty:
  active_mode_df = active_mode_df[
      ~active_mode_df["Date"]
      .dt.day_name()
      .isin(st.session_state["excluded_days"])
  ]

if st.session_state["excluded_dates"] and not active_mode_df.empty:
  ex_date_strs = [
      pd.to_datetime(d).date() for d in st.session_state["excluded_dates"]
  ]
  active_mode_df = active_mode_df[
      ~active_mode_df["Date"].dt.date.isin(ex_date_strs)
  ]

trend_df = active_mode_df.sort_values("Date", ascending=True)

# =========================================================
# KPI SELECTION PANEL
# =========================================================
with st.container():
  st.markdown("<div class='main-card'>", unsafe_allow_html=True)

  hdr1, hdr2, hdr3 = st.columns([1.5, 3.5, 1.5])

  with hdr1:
    st.markdown(
        "<h3 style='margin:0; padding-top:4px;'>Select KPIs</h3>",
        unsafe_allow_html=True,
    )

  with hdr2:
    search_selected_kpi = st.selectbox(
        "Search KPIs...",
        options=[""] + all_kpi_options,
        index=0,
        placeholder="🔍 Type or select KPI to search and highlight...",
        label_visibility="collapsed",
        key="kpi_autosuggest_search",
    )

    if search_selected_kpi:
      for cat, data in KPI_GROUPS.items():
        if search_selected_kpi in data["metrics"]:
          if search_selected_kpi not in st.session_state[f"selected_{cat}"]:
            st.session_state[f"selected_{cat}"].append(search_selected_kpi)
            st.session_state[f"pills_{cat}"] = st.session_state[
                f"selected_{cat}"
            ]
            st.rerun()

  with hdr3:
    if st.button(
        "🔄 Reset Defaults", key="reset_top", use_container_width=True
    ):
      reset_to_strict_defaults()
      st.rerun()

  st.markdown(
      "<hr style='margin: 12px 0 16px 0; border-color: #f1f5f9;'>",
      unsafe_allow_html=True,
  )

  for cat, data in KPI_GROUPS.items():
    available_metrics = [m for m in data["metrics"] if m in df.columns]

    show_more_key = f"more_{cat}"
    if show_more_key not in st.session_state:
      st.session_state[show_more_key] = False

    limit = len(available_metrics) if st.session_state[show_more_key] else 5
    visible_metrics = available_metrics[:limit]

    col_label, col_chips, col_more = st.columns([1.5, 7.7, 0.8])

    with col_label:
      st.markdown(
          f"<div class='row-header'><span>{data['icon']}</span> {cat}</div>",
          unsafe_allow_html=True,
      )

    with col_chips:
      selected_pills = st.pills(
          label=cat,
          options=visible_metrics,
          default=[
              m
              for m in st.session_state[f"selected_{cat}"]
              if m in visible_metrics
          ],
          selection_mode="multi",
          key=f"pills_{cat}",
          label_visibility="collapsed",
      )

      overflow_selected = [
          m
          for m in st.session_state[f"selected_{cat}"]
          if m in available_metrics and m not in visible_metrics
      ]
      st.session_state[f"selected_{cat}"] = selected_pills + overflow_selected

    with col_more:
      if len(available_metrics) > 5:
        is_toggled = st.toggle(
            "More",
            value=st.session_state[show_more_key],
            key=f"toggle_{cat}",
        )
        if is_toggled != st.session_state[show_more_key]:
          st.session_state[show_more_key] = is_toggled
          st.rerun()

    st.markdown(
        "<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True
    )

  st.markdown("</div>", unsafe_allow_html=True)

# Active Selected KPIs
active_selected_kpis = []
for cat in KPI_GROUPS.keys():
  for metric in st.session_state[f"selected_{cat}"]:
    if metric not in active_selected_kpis:
      active_selected_kpis.append(metric)

for c_name in st.session_state["custom_kpis_dict"].keys():
  if c_name not in active_selected_kpis:
    active_selected_kpis.append(c_name)

# =========================================================
# DASHBOARD TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(
    ["⚡ Dynamic Performance Table", "📈 Trend Visualizations", "📋 Raw Sheet Data"]
)

# =========================================================
# TAB 1: DYNAMIC PERFORMANCE ANALYSIS TABLE
# =========================================================
with tab1:
  st.markdown("## ⚡ BL Search RCA DashBoard")

  if not active_selected_kpis:
    st.info("💡 Please select KPI chips above to display the analysis table.")
  elif active_mode_df.empty:
    st.warning("⚠️ No data available for selected mode/dates.")
  else:
    tb1, tb2, tb3, tb4 = st.columns([1.5, 1.2, 1.8, 1.2])

    with tb1:
      transpose = st.toggle("⇄ Transpose Table", value=False)

    with tb2:
      if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    with tb3:
      with st.popover("➕ Add Calc KPI", use_container_width=True):
        st.caption("Create a dynamic metric from existing data.")

        all_numeric_cols = [c for c in df.columns if c != "Date"]

        base_metric = st.selectbox(
            "Base Metric (A)", all_numeric_cols, key="calc_base_m"
        )
        op_selected = st.selectbox(
            "Operation",
            [
                "÷ (Ratio A/B)",
                "× (Multiply A*B)",
                "+ (Add A+B)",
                "- (Subtract A-B)",
            ],
            key="calc_op",
        )
        sec_metric = st.selectbox(
            "Secondary Metric (B)", all_numeric_cols, key="calc_sec_m"
        )
        new_name = st.text_input(
            "New Metric Name", value="Custom Ratio", key="calc_name_input"
        ).strip()

        if st.button("Create Custom KPI", use_container_width=True):
          if new_name:
            st.session_state["custom_kpis_dict"][new_name] = {
                "a": base_metric,
                "op": op_selected,
                "b": sec_metric,
            }
            st.rerun()

    with tb4:
      st.button("📝 Comment", use_container_width=True)

    base_df = active_mode_df[["Date"] + active_selected_kpis].copy()
    avg_values = base_df[active_selected_kpis].mean()

    best_values = {}
    for col in active_selected_kpis:
      if "zero" in col.lower() or "position" in col.lower():
        best_values[col] = df[col].min()
      else:
        best_values[col] = df[col].max()

    def fmt_val(val, metric):
      if (
          "%" in metric
          or "Txn/100" in metric
          or "Transactor/" in metric
          or "Ratio" in metric
          or "NI/TXN" in metric
      ):
        return f"{val:.1f}%"
      elif val > 1000:
        return f"{val:,.0f}" if val.is_integer() else f"{val:,.2f}"
      else:
        return f"{val:.2f}".rstrip("0").rstrip(".")

    if not transpose:
      html_code = (
          "<div class='custom-table-container'><table class='custom-table'>"
      )
      html_code += "<thead><tr><th>Date</th>"
      for metric in active_selected_kpis:
        html_code += f"<th>{metric}</th>"
      html_code += "</tr></thead><tbody>"

      prev_row = None

      for idx_num, (idx, row) in enumerate(base_df.iterrows()):
        date_str = (
            row["Date"].strftime("%Y-%m-%d - %a")
            if mode_view_type != "wow"
            else f"Week of {row['Date'].strftime('%Y-%m-%d')} - Weekly Avg"
        )
        html_code += f"<tr><td style='font-weight:700;'>{date_str}</td>"

        for metric in active_selected_kpis:
          val = row[metric]
          formatted = fmt_val(val, metric)

          if idx_num == 0:
            html_code += f"<td>{formatted}</td>"
          else:
            ref_val = prev_row[metric] if prev_row is not None else 0
            pct_change = (
                ((val - ref_val) / ref_val) * 100 if ref_val != 0 else 0
            )

            badge_cls = (
                "badge-pos"
                if pct_change > 0
                else ("badge-neg" if pct_change < 0 else "badge-neutral")
            )
            badge = f"<span class='{badge_cls}'>{pct_change:+.1f}%</span>"

            sub_avg_html = ""
            if idx_num == len(base_df) - 1 and mode_view_type != "date_range":
              avg_v = avg_values[metric]
              vs_avg_pct = ((val - avg_v) / avg_v) * 100 if avg_v != 0 else 0
              sub_cls = "sub-avg-pos" if vs_avg_pct >= 0 else "sub-avg-neg"
              sub_avg_html = (
                  f"<span class='{sub_cls}'>vs Avg: {vs_avg_pct:+.1f}%</span>"
              )

            html_code += f"<td>{formatted} {badge}{sub_avg_html}</td>"

        prev_row = row
        html_code += "</tr>"

      avg_lbl = (
          "Average of Selected Weeks"
          if mode_view_type == "wow"
          else "Average of Selected Period"
      )
      html_code += f"<tr class='avg-row'><td>{avg_lbl}</td>"
      for metric in active_selected_kpis:
        html_code += f"<td>{fmt_val(avg_values[metric], metric)}</td>"
      html_code += "</tr>"

      best_lbl = (
          "Best Ever (Weekly Avg)"
          if mode_view_type == "wow"
          else "Best Ever (Daily)"
      )
      html_code += (
          f"<tr class='best-row'><td style='color:#0284c7;"
          f" font-weight:800;'>{best_lbl}</td>"
      )
      for metric in active_selected_kpis:
        html_code += (
            f"<td style='color:#0284c7;"
            f" font-weight:800;'>{fmt_val(best_values[metric], metric)}</td>"
        )
      html_code += "</tr>"

      html_code += "</tbody></table></div>"

    else:
      html_code = (
          "<div class='custom-table-container'><table class='custom-table'>"
      )
      html_code += "<thead><tr><th>KPI / Metric</th>"

      for idx, row in base_df.iterrows():
        d_lbl = (
            row["Date"].strftime("%Y-%m-%d")
            if mode_view_type != "wow"
            else f"Wk {row['Date'].strftime('%m-%d')}"
        )
        html_code += f"<th>{d_lbl}</th>"
      html_code += "<th>Avg</th><th>Best Ever</th></tr></thead><tbody>"

      for metric in active_selected_kpis:
        html_code += (
            f"<tr><td style='font-weight:700; text-align:left;"
            f" padding-left:16px;'>{metric}</td>"
        )

        prev_val = None
        for idx_num, (idx, row) in enumerate(base_df.iterrows()):
          val = row[metric]
          formatted = fmt_val(val, metric)

          if idx_num == 0:
            html_code += f"<td>{formatted}</td>"
          else:
            pct_change = (
                ((val - prev_val) / prev_val * 100)
                if prev_val != 0 and prev_val is not None
                else 0
            )
            badge_cls = "badge-pos" if pct_change >= 0 else "badge-neg"
            badge = f"<span class='{badge_cls}'>{pct_change:+.1f}%</span>"
            html_code += f"<td>{formatted} {badge}</td>"

          prev_val = val

        html_code += f"<td style='font-weight:700;'>{fmt_val(avg_values[metric], metric)}</td>"
        html_code += (
            f"<td style='color:#0284c7;"
            f" font-weight:800;'>{fmt_val(best_values[metric], metric)}</td></tr>"
        )

      html_code += "</tbody></table></div>"

    st.markdown(html_code, unsafe_allow_html=True)

# =========================================================
# TAB 2: TREND ANALYSIS (FIXED PLOTLY RGBA COLOR VALIDATION)
# =========================================================
with tab2:
  st.markdown("## 📈 Trend Visualizations")

  if not active_selected_kpis:
    st.info("💡 Select KPI chips above to display visual trends.")
  elif trend_df.empty:
    st.warning("⚠️ No data available for selected mode/dates.")
  else:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
      chart_type = st.radio(
          "Chart Style", ["Line Chart", "Bar Chart"], horizontal=True
      )

    x_dates_formatted = (
        trend_df["Date"].dt.strftime("%Y-%m-%d - %a")
        if mode_view_type != "wow"
        else trend_df["Date"].dt.strftime("Week of %Y-%m-%d - Weekly Avg")
    )

    st.markdown("### Combined Overview")
    fig = go.Figure()
    for metric in active_selected_kpis:
      if metric in trend_df.columns:
        if chart_type == "Line Chart":
          fig.add_trace(
              go.Scatter(
                  x=x_dates_formatted,
                  y=trend_df[metric],
                  mode="lines+markers",
                  name=metric,
              )
          )
        else:
          fig.add_trace(
              go.Bar(
                  x=x_dates_formatted,
                  y=trend_df[metric],
                  name=metric,
              )
          )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        height=480,
        font=dict(size=14),
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(type="category"),
        yaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr style='margin: 24px 0;'>", unsafe_allow_html=True)
    st.markdown("### Individual Breakdown Trends")

    # FIXED: Valid rgba(...) strings for Plotly compatibility
    theme_colors = [
        {"line": "#0284c7", "fill": "rgba(2, 132, 197, 0.12)"},
        {"line": "#7c3aed", "fill": "rgba(124, 58, 237, 0.12)"},
        {"line": "#10b981", "fill": "rgba(16, 185, 129, 0.12)"},
        {"line": "#ef4444", "fill": "rgba(239, 68, 68, 0.12)"},
        {"line": "#f59e0b", "fill": "rgba(245, 158, 11, 0.12)"},
    ]

    ind_cols = st.columns(2)
    for idx, metric in enumerate(active_selected_kpis):
      if metric in trend_df.columns:
        palette = theme_colors[idx % len(theme_colors)]

        is_pos_or_rank = "position" in metric.lower() or "rank" in metric.lower()
        is_percent = (
            "%" in metric
            or "txn/100" in metric.lower()
            or "transactor/" in metric.lower()
            or "ratio" in metric.lower()
            or "ni/txn" in metric.lower()
        )

        with ind_cols[idx % 2]:
          st.markdown(f"#### {metric}")
          fig_ind = go.Figure()

          if chart_type == "Line Chart":
            fig_ind.add_trace(
                go.Scatter(
                    x=x_dates_formatted,
                    y=trend_df[metric],
                    mode="lines+markers",
                    name=metric,
                    line=dict(color=palette["line"], width=2.5),
                    fill="tozeroy" if not is_pos_or_rank else "none",
                    fillcolor=palette["fill"],
                )
            )
          else:
            fig_ind.add_trace(
                go.Bar(
                    x=x_dates_formatted,
                    y=trend_df[metric],
                    name=metric,
                    marker=dict(color=palette["line"]),
                )
            )

          yaxis_dict = dict(gridcolor="#f1f5f9")
          if not is_pos_or_rank:
            yaxis_dict["rangemode"] = "tozero"
            if is_percent:
              max_v = trend_df[metric].max()
              yaxis_dict["range"] = [0, max(max_v * 1.25, 10)]

          fig_ind.update_layout(
              template="plotly_white",
              hovermode="x unified",
              height=320,
              font=dict(size=12),
              margin=dict(l=20, r=20, t=20, b=20),
              showlegend=False,
              xaxis=dict(type="category", gridcolor="#f1f5f9"),
              yaxis=yaxis_dict,
          )
          st.plotly_chart(fig_ind, use_container_width=True)

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