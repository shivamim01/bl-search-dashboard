import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="BL Search Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    font-size: 20px !important;
}

/* MAIN TITLES */
h1 {
    font-size: 54px !important;
    font-weight: 800 !important;
}

h2 {
    font-size: 38px !important;
    font-weight: 700 !important;
}

h3 {
    font-size: 30px !important;
    font-weight: 700 !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    width: 420px !important;
    background: #ffffff;
    border-right: 1px solid #eef2f7;
}

/* SIDEBAR LABELS */
section[data-testid="stSidebar"] label {
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* INPUTS */
.stSelectbox label,
.stDateInput label,
.stMultiSelect label {
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* SELECT BOX */
div[data-baseweb="select"] {
    font-size: 18px !important;
}

/* CHECKBOX */
.stCheckbox label {
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* BUTTONS */
.stButton button {
    border-radius: 14px !important;
    height: 52px !important;
    font-size: 17px !important;
    font-weight: 700 !important;
}

/* METRIC CARDS */
.metric-card {
    background: white;
    border-radius: 24px;
    padding: 34px;
    text-align: center;
    box-shadow: 0px 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
}

.metric-value {
    font-size: 64px;
    font-weight: 800;
    color: #111827;
}

.metric-label {
    font-size: 22px;
    color: #6b7280;
    margin-bottom: 12px;
}

/* TABLES */
thead tr th {
    font-size: 20px !important;
    font-weight: 700 !important;
    padding: 22px !important;
}

tbody tr td {
    font-size: 18px !important;
    padding: 20px !important;
}

/* SECTION TITLES */
.section-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 24px;
    color: #111827;
}

/* SUBTITLE */
.small-subtitle {
    color: #6b7280;
    font-size: 24px;
    margin-bottom: 24px;
}

/* CHART AREA */
.js-plotly-plot {
    zoom: 1.12;
}

.main {
    background-color: #f5f7fb;
}

section[data-testid="stSidebar"] {
    width: 380px !important;
    background: #ffffff;
    border-right: 1px solid #eef2f7;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 100%;
}

h1, h2, h3 {
    color: #111827;
    font-weight: 700;
}

.card {
    background: white;
    border-radius: 22px;
    padding: 28px;
    box-shadow: 0px 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
}

.control-card {
    background: white;
    border-radius: 26px;
    padding: 28px;
    box-shadow: 0px 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #eef2f7;
    margin-bottom: 24px;
}

.metric-card {
    background: white;
    border-radius: 22px;
    padding: 28px;
    text-align: center;
    box-shadow: 0px 4px 12px rgba(15, 23, 42, 0.05);
    border: 1px solid #eef2f7;
}

.metric-value {
    font-size: 52px;
    font-weight: 700;
    color: #111827;
}

.metric-label {
    font-size: 18px;
    color: #6b7280;
    margin-bottom: 10px;
}

.section-title {
    font-size: 34px;
    font-weight: 700;
    margin-bottom: 20px;
    color: #111827;
}

.small-subtitle {
    color: #6b7280;
    font-size: 20px;
    margin-bottom: 16px;
}

.green-badge {
    background: #dcfce7;
    color: #15803d;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
}

.red-badge {
    background: #fee2e2;
    color: #dc2626;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 18px;
    overflow: hidden;
}

thead tr th {
    font-size: 18px !important;
    font-weight: 700 !important;
    padding: 18px !important;
    background: #f8fafc;
}

tbody tr td {
    font-size: 17px !important;
    padding: 18px !important;
}

.stButton button {
    border-radius: 14px !important;
    height: 48px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}

.stCheckbox label {
    font-size: 16px !important;
    font-weight: 600;
}

div[data-baseweb="select"] * {
    cursor: pointer !important;
}

div[data-baseweb="input"] * {
    cursor: pointer !important;
}

input {
    cursor: pointer !important;
}

select {
    cursor: pointer !important;
}

.metric-card {
    background: white;
    padding: 28px;
    border-radius: 18px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    text-align: center;
}

.metric-label {
    font-size: 18px;
    color: #6B7280;
    font-weight: 600;
    margin-bottom: 18px;
}

.metric-value {
    font-size: 42px;
    font-weight: 800;
    color: #111827;
}

.green-badge {
    background: #DCFCE7;
    color: #15803D;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 16px;
    font-weight: 700;
}

.red-badge {
    background: #FEE2E2;
    color: #DC2626;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 16px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DATA LOAD
# =========================================================
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vThPxxJxqepKKuCVQuLX67chDHIbaA6jnF9ggTcA0qGAM0hpezfsx3s-ZfkGKsl0ukrGQ0vs7I_A81L/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data():

    df = pd.read_csv(csv_url)

    df = df[df["Date"] != "Average"]

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df = df.dropna(subset=["Date"])

    for col in df.columns:

        if col != "Date":

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "")
                .replace("None", "0")
                .replace("#REF!", "0")
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    df = df.sort_values("Date")

    return df

df = load_data()

# =========================================================
# KPI DEFINITIONS
# =========================================================
SEARCH_KPIS = [
    "Trade Searches",
    "Seller Searches",
    "Mobile Searches",
    "Android Searches",
    "IOS Searches",
    "Total Searches",
    "Searches excluding top 20 Sellers",
    "Daily Active searchers",
    "Final Zero Result Search",
    "Numeric Searches"
]

TXN_KPIS = [
    "BL Search API Txn",
    "bl search txn",
    "Android",
    "Desktop",
    "iOS",
    "Unique Transactors",
    "Txn from Top 10 position",
    "Bizfeed Txn - BL search page",
    "Numeric Searches Txn"
]

# =========================================================
# DERIVED KPIs
# =========================================================
if (
    "BL Search API Txn" in df.columns and
    "Searches excluding top 20 Sellers" in df.columns
):
    df["Txn/100 Searches - removing top 20"] = (
        df["BL Search API Txn"]
        /
        df["Searches excluding top 20 Sellers"]
    ) * 100

if (
    "Txn from Top 10 position" in df.columns and
    "BL Search API Txn" in df.columns
):
    df["Txn from Top 10 position in %"] = (
        df["Txn from Top 10 position"]
        /
        df["BL Search API Txn"]
    ) * 100

if (
    "Final Zero Result Search" in df.columns and
    "Searches excluding top 20 Sellers" in df.columns
):
    df["Zero Search Result % after removing top 20 sellers"] = (
        df["Final Zero Result Search"]
        /
        df["Searches excluding top 20 Sellers"]
    ) * 100

if (
    "Numeric Searches Txn" in df.columns and
    "Numeric Searches" in df.columns
):
    df["Numeric Searches Txn/100 Searches"] = (
        df["Numeric Searches Txn"]
        /
        df["Numeric Searches"]
    ) * 100

KPI_METRICS = [
    "Txn/100 Searches - removing top 20",
    "Mean Purchase Position - Search",
    "Txn from Top 10 position in %",
    "Zero Search Result % after removing top 20 sellers",
    "Numeric Searches Txn/100 Searches"
]

# =========================================================
# SESSION STATE
# =========================================================
if "selected_searches" not in st.session_state:
    st.session_state.selected_searches = []

if "selected_txns" not in st.session_state:
    st.session_state.selected_txns = []

if "selected_kpis" not in st.session_state:
    st.session_state.selected_kpis = []

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown(
    "<h1 style='font-size:32px;'>Dashboard Filters</h1>",
    unsafe_allow_html=True
)

# =========================================================
# CHIP FUNCTION
# =========================================================
def chip_selector(section_name, items, state_key):

    st.sidebar.markdown(f"### {section_name}")

    cols = st.sidebar.columns(2)

    for idx, item in enumerate(items):

        if item not in df.columns and item not in KPI_METRICS:
            continue

        with cols[idx % 2]:

            checked = st.checkbox(
                item,
                value=item in st.session_state[state_key],
                key=f"{state_key}_{item}"
            )

            if checked:

                if item not in st.session_state[state_key]:
                    st.session_state[state_key].append(item)

            else:

                if item in st.session_state[state_key]:
                    st.session_state[state_key].remove(item)

# =========================================================
# SIDEBAR SECTIONS
# =========================================================
chip_selector(
    "Searches Data",
    SEARCH_KPIS,
    "selected_searches"
)

st.sidebar.markdown("---")

chip_selector(
    "Txn Data",
    TXN_KPIS,
    "selected_txns"
)

st.sidebar.markdown("---")

chip_selector(
    "KPIs",
    KPI_METRICS,
    "selected_kpis"
)

# =========================================================
# HEADER
# =========================================================
st.title("📊 BL Search Dashboard")

st.markdown(
    "<div class='small-subtitle'>Real-time BL Search KPIs from automated Google Sheets</div>",
    unsafe_allow_html=True
)

# =========================================================
# CONTROL PANEL
# =========================================================
with st.container():

    top1, top2 = st.columns(2)

    with top1:
        selected_date = st.date_input(
            "Select Date",
            value=df["Date"].max().date()
        )

    with top2:
        weeks_compare = st.selectbox(
            "Weeks to Compare",
            list(range(1, 9)),
            index=3
        )

# =========================================================
# DATE COMPARISON
# =========================================================
selected_date = pd.to_datetime(selected_date)

comparison_dates = [selected_date]

for i in range(1, weeks_compare):
    comparison_dates.append(
        selected_date - timedelta(days=7*i)
    )

comparison_df = df[
    df["Date"].dt.date.isin(
        [d.date() for d in comparison_dates]
    )
]

comparison_df = comparison_df.sort_values(
    "Date",
    ascending=False
)

# =========================================================
# KPI CARDS
# =========================================================

st.markdown("## Executive KPI Overview")

card_metrics = [
    "Searches excluding top 20 Sellers",
    "Daily Active searchers",
    "Final Zero Result Search",
    "BL Search API Txn",
    "Unique Transactors",
    "Txn/100 Searches - removing top 20",
    "Zero Search Result % after removing top 20 sellers",
    "Numeric Searches Txn/100 Searches"
]

# =========================================================
# USE SELECTED DATE
# =========================================================

selected_df = df[df["Date"] == selected_date]

if len(selected_df) > 0:
    latest = selected_df.iloc[0]
else:
    latest = df.iloc[-1]

previous_df = df[df["Date"] < latest["Date"]]

if len(previous_df) > 0:
    previous = previous_df.iloc[-1]
else:
    previous = latest

for i in range(0, len(card_metrics), 4):

    cols = st.columns(4)

    for j in range(4):

        if i + j >= len(card_metrics):
            continue

        metric = card_metrics[i + j]

        if metric not in df.columns:
            continue

        current = latest[metric]
        prev = previous[metric]

        delta = current - prev

        if prev != 0:
            delta_pct = (delta / prev) * 100
        else:
            delta_pct = 0

        positive = delta >= 0

        badge_color = "#DCFCE7" if positive else "#FEE2E2"
        text_color = "#15803D" if positive else "#DC2626"

        arrow = "↑" if positive else "↓"

        if "%" in metric or "Txn/100" in metric:
            value = f"{current:.2f}"
        else:
            value = f"{int(current):,}"

        with cols[j]:

            st.markdown(
                f"""
<div style="
background:white;
padding:28px;
border-radius:18px;
border:1px solid #E5E7EB;
box-shadow:0 2px 8px rgba(0,0,0,0.04);
text-align:center;
min-height:220px;
">

<div style="
font-size:18px;
color:#6B7280;
font-weight:600;
margin-bottom:20px;
">
{metric}
</div>

<div style="
font-size:42px;
font-weight:800;
color:#111827;
margin-bottom:18px;
">
{value}
</div>

<span style="
background:{badge_color};
color:{text_color};
padding:8px 14px;
border-radius:999px;
font-size:16px;
font-weight:700;
">
{arrow} {abs(delta_pct):.2f}%
</span>

</div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📊 KPI Comparison",
    "📈 Trend Analysis",
    "📋 Raw Data"
])

# =========================================================
# TABLE FUNCTION
# =========================================================
def build_comparison_table(metrics, title):

    st.markdown(
        f"<div class='section-title'>{title}</div>",
        unsafe_allow_html=True
    )

    if len(metrics) == 0:

        st.info("Select metrics from sidebar")

        return

    table_df = comparison_df[
        ["Date"] + metrics
    ].copy()

    table_df["Date"] = table_df["Date"].dt.strftime(
        "%Y-%m-%d - %a"
    )

    current_row = table_df.iloc[0]

    show_changes = st.toggle(
        "Show % Changes",
        value=True,
        key=f"toggle_{title}"
    )

    col1, col2, col3 = st.columns([1,1,2])

    with col1:

        transpose = st.button(
            "Transpose Table",
            use_container_width=True,
            key=f"transpose_{title}"
        )

    with col2:

        calculate = st.button(
            "Calculate Field",
            use_container_width=True,
            key=f"calc_{title}"
        )

    with col3:

        st.download_button(
            "⬇ Export CSV",
            data=table_df.to_csv(index=False),
            file_name=f"{title}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # =====================================================
    # SHOW CHANGES
    # =====================================================
    if show_changes:

        for metric in metrics:

            formatted_values = []

            current_value = current_row[metric]

            for idx, row in table_df.iterrows():

                value = row[metric]

                if idx == 0:

                    formatted_values.append(
                        f"{value:,.0f}"
                    )

                else:

                    pct = 0

                    if current_value != 0:

                        pct = (
                            (value - current_value)
                            / current_value
                        ) * 100

                    arrow = (
                        "↑"
                        if pct > 0
                        else "↓"
                    )

                    badge_class = (
                        "green-badge"
                        if pct > 0
                        else "red-badge"
                    )

                    formatted = (
                        f"{value:,.0f}  "
                        f"{arrow} {abs(pct):.1f}%"
                    )

                    formatted_values.append(formatted)

            table_df[metric] = formatted_values

    # =====================================================
    # AVERAGE ROW
    # =====================================================
    avg_row = {
        "Date": f"Average of past {weeks_compare-1} weeks"
    }

    for metric in metrics:

        avg_value = comparison_df.iloc[1:][metric].mean()

        avg_row[metric] = f"{avg_value:,.2f}"

    table_df.loc[len(table_df)] = avg_row

    # =====================================================
    # TRANSPOSE
    # =====================================================
    if transpose:

        table_df = (
            table_df
            .set_index("Date")
            .T
            .reset_index()
        )

    # =====================================================
    # CALCULATE FIELD
    # =====================================================
    if calculate:

        try:

            numeric_df = comparison_df[metrics]

            table_df["Average"] = (
                numeric_df.mean(axis=1)
                .round(2)
                .astype(str)
            )

        except:
            pass

    st.markdown("<br>", unsafe_allow_html=True)

    st.dataframe(
        table_df,
        use_container_width=True,
        height=500
    )

# =========================================================
# KPI COMPARISON TAB
# =========================================================
with tab1:

    build_comparison_table(
        st.session_state.selected_searches,
        "Searches"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    build_comparison_table(
        st.session_state.selected_txns,
        "Transactions"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    build_comparison_table(
        st.session_state.selected_kpis,
        "KPIs"
    )

# =========================================================
# CHART FUNCTION
# =========================================================
def build_chart(metrics, title):

    st.markdown(
        "<div class='card'>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<div class='section-title'>{title}</div>",
        unsafe_allow_html=True
    )

    if len(metrics) == 0:

        st.info(
            "Select metrics from sidebar to visualize trends"
        )

        st.markdown("</div>", unsafe_allow_html=True)

        return

    fig = go.Figure()

    for metric in metrics:

        if metric not in df.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df[metric],
                mode="lines+markers",
                name=metric
            )
        )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        height=600,
        legend_title="Metrics",
        font=dict(size=16),
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TREND ANALYSIS TAB
# =========================================================
with tab2:

    build_chart(
        st.session_state.selected_searches,
        "Search Trends"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    build_chart(
        st.session_state.selected_txns,
        "Transaction Trends"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    build_chart(
        st.session_state.selected_kpis,
        "KPI Trends"
    )

# =========================================================
# RAW DATA TAB
# =========================================================
with tab3:

    st.markdown(
        "<div class='section-title'>Raw Data</div>",
        unsafe_allow_html=True
    )

    search_text = st.text_input(
        "Search Data"
    )

    raw_df = df.copy()

    if search_text:

        raw_df = raw_df[
            raw_df.astype(str)
            .apply(
                lambda x:
                x.str.contains(
                    search_text,
                    case=False
                )
            )
            .any(axis=1)
        ]

    st.download_button(
        "⬇ Download Full CSV",
        data=raw_df.to_csv(index=False),
        file_name="bl_search_dashboard.csv",
        mime="text/csv"
    )

    st.dataframe(
        raw_df,
        use_container_width=True,
        height=700
    )