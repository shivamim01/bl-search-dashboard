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
# CUSTOM CSS FOR MATCHING TABLE & CHIP UI
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

/* CUSTOM STYLING FOR NATIVE STREAMLIT PILLS */
div[data-testid="stPills"] button {
    font-size: 16px !important;
    font-weight: 600 !important;
    border-radius: 999px !important;
    padding: 6px 18px !important;
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
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    margin-top: 16px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
    text-align: center;
    font-size: 18px;
}

.custom-table th {
    background-color: #f8fafc;
    color: #475569;
    font-weight: 700;
    padding: 18px 16px;
    border-bottom: 1.5px solid #e2e8f0;
    border-right: 1px solid #f1f5f9;
}

.custom-table td {
    padding: 16px 14px;
    border-bottom: 1px solid #f1f5f9;
    border-right: 1px solid #f1f5f9;
    color: #1e293b;
    vertical-align: middle;
}

.custom-table tr:hover {
    background-color: #f8fafc;
}

/* PERCENTAGE BADGES */
.badge-pos {
    color: #10b981;
    font-weight: 700;
    font-size: 16px;
    margin-left: 6px;
}

.badge-neg {
    color: #ef4444;
    font-weight: 700;
    font-size: 16px;
    margin-left: 6px;
}

.badge-neutral {
    color: #94a3b8;
    font-weight: 600;
    font-size: 16px;
    margin-left: 6px;
}

.sub-avg-pos {
    display: block;
    font-size: 14px;
    color: #10b981;
    font-weight: 600;
    margin-top: 2px;
}

.sub-avg-neg {
    display: block;
    font-size: 14px;
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

def reset_to_strict_defaults():
  for cat, data in KPI_GROUPS.items():
    st.session_state[f"selected_{cat}"] = [
        d for d in data["defaults"] if d in df.columns
    ]
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

# =========================================================
# DASHBOARD TITLE
# =========================================================
st.title("⚡ Dynamic Performance Analytics")

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
# KPI SELECTION PANEL
# =========================================================
with st.container():
  st.markdown("<div class='main-card'>", unsafe_allow_html=True)

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
    if st.button("🔄 Reset Defaults", key="reset_top", use_container_width=True):
      reset_to_strict_defaults()
      st.rerun()

  st.markdown("<hr style='margin: 16px 0 24px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)

  for cat, data in KPI_GROUPS.items():
    available_metrics = [m for m in data["metrics"] if m in df.columns]

    if search_query:
      available_metrics = [
          m for m in available_metrics if search_query in m.lower()
      ]
      if not available_metrics:
        continue

    show_more_key = f"more_{cat}"
    if show_more_key not in st.session_state:
      st.session_state[show_more_key] = False

    limit = len(available_metrics) if st.session_state[show_more_key] else 5
    visible_metrics = available_metrics[:limit]

    col_label, col_chips, col_more = st.columns([2.2, 7, 1])

    with col_label:
      st.markdown(
          f"<div class='row-header'><span>{data['icon']}</span> {cat}</div>",
          unsafe_allow_html=True,
      )

    with col_chips:
      selected_pills = st.pills(
          label=cat,
          options=visible_metrics,
          default=[m for m in st.session_state[f"selected_{cat}"] if m in visible_metrics],
          selection_mode="multi",
          key=f"pills_{cat}",
          label_visibility="collapsed",
      )
      
      overflow_selected = [
          m for m in st.session_state[f"selected_{cat}"] if m in available_metrics and m not in visible_metrics
      ]
      st.session_state[f"selected_{cat}"] = selected_pills + overflow_selected

    with col_more:
      if len(available_metrics) > 5:
        is_toggled = st.toggle("More", value=st.session_state[show_more_key], key=f"toggle_{cat}")
        if is_toggled != st.session_state[show_more_key]:
          st.session_state[show_more_key] = is_toggled
          st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

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
  st.markdown("## ⚡ Dynamic Performance Analysis Table")

  if not active_selected_kpis:
    st.info("💡 Please select KPI chips above to display the analysis table.")
  else:
    tb1, tb2, tb3, tb4, tb5 = st.columns([1.5, 1.2, 1.2, 1.8, 1.2])

    with tb1:
      transpose = st.toggle("⇄ Transpose Table", value=False)

    with tb2:
      if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    with tb3:
      if st.button("⏮ Reset KPIs", use_container_width=True):
        reset_to_strict_defaults()
        st.rerun()

    with tb4:
      with st.popover("➕ Add Calc KPI", use_container_width=True):
        st.caption("Create a dynamic metric from existing data.")
        
        all_numeric_cols = [c for c in df.columns if c != "Date"]
        
        base_metric = st.selectbox("Base Metric (A)", all_numeric_cols, key="calc_base_m")
        op_selected = st.selectbox("Operation", ["÷ (Ratio A/B)", "× (Multiply A*B)", "+ (Add A+B)", "- (Subtract A-B)"], key="calc_op")
        sec_metric = st.selectbox("Secondary Metric (B)", all_numeric_cols, key="calc_sec_m")
        new_name = st.text_input("New Metric Name", value="Custom Ratio", key="calc_name_input").strip()

        if st.button("Create Custom KPI", use_container_width=True):
          if new_name:
            st.session_state["custom_kpis_dict"][new_name] = {
                "a": base_metric,
                "op": op_selected,
                "b": sec_metric
            }
            st.rerun()

    with tb5:
      st.button("📝 Comment", use_container_width=True)

    base_df = comparison_df[["Date"] + active_selected_kpis].copy()
    avg_values = base_df[active_selected_kpis].mean()
    
    best_values = {}
    for col in active_selected_kpis:
      if "zero" in col.lower() or "position" in col.lower():
        best_values[col] = df[col].min()
      else:
        best_values[col] = df[col].max()

    def fmt_val(val, metric):
      if "%" in metric or "Txn/100" in metric or "Transactor/" in metric or "Ratio" in metric or "NI/TXN" in metric:
        return f"{val:.1f}%"
      elif val > 1000:
        return f"{val:,.0f}"
      else:
        return f"{val:.2f}".rstrip('0').rstrip('.')

    if not transpose:
      html_code = "<div class='custom-table-container'><table class='custom-table'>"
      html_code += "<thead><tr><th>Date</th>"
      for metric in active_selected_kpis:
        html_code += f"<th>{metric}</th>"
      html_code += "</tr></thead><tbody>"

      base_row = base_df.iloc[0] if len(base_df) > 0 else None

      for idx, row in base_df.iterrows():
        date_str = row["Date"].strftime("%Y-%m-%d - %a")
        html_code += f"<tr><td style='font-weight:700;'>{date_str}</td>"

        for metric in active_selected_kpis:
          val = row[metric]
          formatted = fmt_val(val, metric)

          if idx == base_df.index[0]:
            html_code += f"<td>{formatted}</td>"
          else:
            base_val = base_row[metric] if base_row is not None else 0
            pct_change = (((val - base_val) / base_val) * 100) if base_val != 0 else 0

            badge_cls = "badge-pos" if pct_change > 0 else ("badge-neg" if pct_change < 0 else "badge-neutral")
            badge = f"<span class='{badge_cls}'>{pct_change:+.1f}%</span>"

            sub_avg_html = ""
            if idx == base_df.index[-1]:
              avg_v = avg_values[metric]
              vs_avg_pct = (((val - avg_v) / avg_v) * 100) if avg_v != 0 else 0
              sub_cls = "sub-avg-pos" if vs_avg_pct >= 0 else "sub-avg-neg"
              sub_avg_html = f"<span class='{sub_cls}'>vs Avg: {vs_avg_pct:+.1f}%</span>"

            html_code += f"<td>{formatted} {badge}{sub_avg_html}</td>"

        html_code += "</tr>"

      html_code += f"<tr class='avg-row'><td>Average of past {weeks_num} weeks</td>"
      for metric in active_selected_kpis:
        html_code += f"<td>{fmt_val(avg_values[metric], metric)}</td>"
      html_code += "</tr>"

      html_code += "<tr class='best-row'><td style='color:#0284c7; font-weight:800;'>Best Ever (Daily)</td>"
      for metric in active_selected_kpis:
        html_code += f"<td style='color:#0284c7; font-weight:800;'>{fmt_val(best_values[metric], metric)}</td>"
      html_code += "</tr>"

      html_code += "tbody></table></div>"

    else:
      html_code = "<div class='custom-table-container'><table class='custom-table'>"
      html_code += "<thead><tr><th>KPI / Metric</th>"
      
      for idx, row in base_df.iterrows():
        html_code += f"<th>{row['Date'].strftime('%Y-%m-%d')}</th>"
      html_code += f"<th>Avg ({weeks_num}W)</th><th>Best Ever</th></tr></thead><tbody>"

      base_row = base_df.iloc[0] if len(base_df) > 0 else None

      for metric in active_selected_kpis:
        html_code += f"<tr><td style='font-weight:700; text-align:left; padding-left:20px;'>{metric}</td>"
        base_val = base_row[metric] if base_row is not None else 0

        for idx, row in base_df.iterrows():
          val = row[metric]
          formatted = fmt_val(val, metric)

          if idx == base_df.index[0]:
            html_code += f"<td>{formatted}</td>"
          else:
            pct_change = ((val - base_val) / base_val * 100) if base_val != 0 else 0
            badge_cls = "badge-pos" if pct_change >= 0 else "badge-neg"
            badge = f"<span class='{badge_cls}'>{pct_change:+.1f}%</span>"
            html_code += f"<td>{formatted} {badge}</td>"

        html_code += f"<td style='font-weight:700;'>{fmt_val(avg_values[metric], metric)}</td>"
        html_code += f"<td style='color:#0284c7; font-weight:800;'>{fmt_val(best_values[metric], metric)}</td></tr>"

      html_code += "tbody></table></div>"

    st.markdown(html_code, unsafe_allow_html=True)

# =========================================================
# TAB 2: TREND ANALYSIS (WITH INDIVIDUAL TRENDS)
# =========================================================
with tab2:
  st.markdown("## 📈 Trend Visualizations")

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

    # 1. COMBINED OVERVIEW CHART
    st.markdown("### Combined Overview")
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
        height=500,
        font=dict(size=18),
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. INDIVIDUAL KPI TREND CHARTS
    st.markdown("<hr style='margin: 32px 0;'>", unsafe_allow_html=True)
    st.markdown("### Individual KPI Trends")

    ind_cols = st.columns(2)
    for idx, metric in enumerate(active_selected_kpis):
      if metric in filtered_trend_df.columns:
        with ind_cols[idx % 2]:
          st.markdown(f"#### {metric}")
          fig_ind = go.Figure()

          if chart_type == "Line Chart":
            fig_ind.add_trace(
                go.Scatter(
                    x=filtered_trend_df["Date"],
                    y=filtered_trend_df[metric],
                    mode="lines+markers",
                    name=metric,
                    line=dict(color="#0284c7", width=3),
                )
            )
          else:
            fig_ind.add_trace(
                go.Bar(
                    x=filtered_trend_df["Date"],
                    y=filtered_trend_df[metric],
                    name=metric,
                    marker=dict(color="#0284c7"),
                )
            )

          fig_ind.update_layout(
              template="plotly_white",
              hovermode="x unified",
              height=380,
              font=dict(size=16),
              margin=dict(l=20, r=20, t=30, b=20),
              showlegend=False,
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