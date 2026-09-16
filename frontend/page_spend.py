"""
Spend Analysis page — interactive charts and tables from the spend dataset.

The page loads the CSV dataset shipped with the project. It also attempts to
fetch data from a backend endpoint if one exists, but gracefully falls back
to the local CSV file.
"""

import os
import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from helpers import get_api_base, api_get



_PALETTE = [
    "#7C3AED", "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
    "#EC4899", "#06B6D4", "#8B5CF6", "#F97316", "#14B8A6",
]

_CARD_CSS = """
<style>
.metric-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 0.85rem;
    padding: 1.25rem 1.5rem;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(124,58,237,0.15);
}
.metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7C3AED, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0.3rem 0;
}
.metric-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
}
</style>
"""




@st.cache_data(ttl=300, show_spinner="Loading spend data…")
def _load_data() -> pd.DataFrame:
    """Load the spend analysis CSV dataset."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "dataset", "spend_analysis_dataset.csv"),
        "/home/ubox48/MultiAgentProject/dataset/spend_analysis_dataset.csv",
    ]
    for path in candidates:
        full = os.path.abspath(path)
        if os.path.isfile(full):
            df = pd.read_csv(full, parse_dates=["PurchaseDate"])
            return df

    st.error("📂 **Dataset not found** — could not locate `spend_analysis_dataset.csv`.")
    return pd.DataFrame()


def _metric_html(label: str, value: str) -> str:
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'</div>'
    )




_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", family="Inter, system-ui, sans-serif"),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def _styled(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT_DEFAULTS)
    fig.update_xaxes(gridcolor="#1E293B", zerolinecolor="#334155")
    fig.update_yaxes(gridcolor="#1E293B", zerolinecolor="#334155")
    return fig




def render():
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Portfolio intelligence</div>', unsafe_allow_html=True)
    st.markdown("# Spend overview")
    st.markdown('<div class="page-intro">Understand where procurement dollars are going, who is buying, and how activity is trending.</div>', unsafe_allow_html=True)

    df = _load_data()
    if df.empty:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filter the portfolio")
    st.sidebar.caption("All visuals update from the selected records.")

    min_date = df["PurchaseDate"].min().date() if "PurchaseDate" in df.columns else datetime.date(2024, 1, 1)
    max_date = df["PurchaseDate"].max().date() if "PurchaseDate" in df.columns else datetime.date(2024, 12, 31)
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    
    categories = sorted(df["Category"].dropna().unique().tolist()) if "Category" in df.columns else []
    selected_cats = st.sidebar.multiselect("Category", options=categories, default=categories)

    suppliers = sorted(df["Supplier"].dropna().unique().tolist()) if "Supplier" in df.columns else []
    selected_suppliers = st.sidebar.multiselect("Supplier", options=suppliers, default=suppliers)

    filtered = df.copy()
    if "PurchaseDate" in filtered.columns and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered = filtered[(filtered["PurchaseDate"] >= start) & (filtered["PurchaseDate"] <= end)]
    if selected_cats and "Category" in filtered.columns:
        filtered = filtered[filtered["Category"].isin(selected_cats)]
    if selected_suppliers and "Supplier" in filtered.columns:
        filtered = filtered[filtered["Supplier"].isin(selected_suppliers)]

    if filtered.empty:
        st.warning("No records match the current filters. Try broadening the date range or categories.")
        return

    total_spend = filtered["TotalCost"].sum() if "TotalCost" in filtered.columns else 0
    total_txns = len(filtered)
    avg_order = total_spend / total_txns if total_txns else 0
    n_suppliers = filtered["Supplier"].nunique() if "Supplier" in filtered.columns else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        st.markdown(_metric_html("Total Spend", f"${total_spend:,.0f}"), unsafe_allow_html=True)
    with c2:
        st.markdown(_metric_html("Transactions", f"{total_txns:,}"), unsafe_allow_html=True)
    with c3:
        st.markdown(_metric_html("Avg Order", f"${avg_order:,.2f}"), unsafe_allow_html=True)
    with c4:
        st.markdown(_metric_html("Suppliers", f"{n_suppliers}"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Portfolio breakdown")
    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        if "Category" in filtered.columns and "TotalCost" in filtered.columns:
            cat_spend = (
                filtered.groupby("Category", as_index=False)["TotalCost"]
                .sum()
                .sort_values("TotalCost", ascending=False)
            )
            fig_bar = px.bar(
                cat_spend, x="Category", y="TotalCost",
                color="Category", color_discrete_sequence=_PALETTE,
                title="Spend by Category",
                labels={"TotalCost": "Total Spend ($)"},
            )
            fig_bar.update_traces(
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
            )
            st.plotly_chart(_styled(fig_bar), use_container_width=True)

    with col_right:
        if "Category" in filtered.columns and "TotalCost" in filtered.columns:
            fig_pie = px.pie(
                cat_spend, names="Category", values="TotalCost",
                color_discrete_sequence=_PALETTE,
                title="Category Mix",
                hole=0.45,
            )
            fig_pie.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
            )
            st.plotly_chart(_styled(fig_pie), use_container_width=True)

    st.markdown("### Momentum and concentration")
    col_left2, col_right2 = st.columns(2, gap="medium")

    with col_left2:
        if "PurchaseDate" in filtered.columns and "TotalCost" in filtered.columns:
            monthly = (
                filtered.set_index("PurchaseDate")
                .resample("M")["TotalCost"]
                .sum()
                .reset_index()
            )
            monthly.columns = ["Month", "TotalCost"]
            fig_line = px.area(
                monthly, x="Month", y="TotalCost",
                title="Monthly Spend Trend",
                labels={"TotalCost": "Total Spend ($)", "Month": ""},
                color_discrete_sequence=["#7C3AED"],
            )
            fig_line.update_traces(
                line=dict(width=2.5),
                fillcolor="rgba(124,58,237,0.12)",
                hovertemplate="<b>%{x|%b %Y}</b><br>$%{y:,.2f}<extra></extra>",
            )
            st.plotly_chart(_styled(fig_line), use_container_width=True)

    with col_right2:
        if "Supplier" in filtered.columns and "TotalCost" in filtered.columns:
            sup_spend = (
                filtered.groupby("Supplier", as_index=False)["TotalCost"]
                .sum()
                .sort_values("TotalCost", ascending=True)
            )
            fig_hbar = px.bar(
                sup_spend, x="TotalCost", y="Supplier",
                orientation="h",
                color="TotalCost", color_continuous_scale=["#1E293B", "#7C3AED"],
                title="Spend by Supplier",
                labels={"TotalCost": "Total Spend ($)"},
            )
            fig_hbar.update_traces(
                hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
            )
            fig_hbar.update_coloraxes(showscale=False)
            st.plotly_chart(_styled(fig_hbar), use_container_width=True)

    st.markdown("### Detail views")
    col_left3, col_right3 = st.columns(2, gap="medium")

    with col_left3:
        if "ItemName" in filtered.columns and "TotalCost" in filtered.columns:
            top_items = (
                filtered.groupby("ItemName", as_index=False)["TotalCost"]
                .sum()
                .sort_values("TotalCost", ascending=False)
                .head(10)
            )
            fig_items = px.bar(
                top_items, x="TotalCost", y="ItemName",
                orientation="h",
                color_discrete_sequence=["#3B82F6"],
                title="Top 10 Items by Spend",
                labels={"TotalCost": "Total Spend ($)", "ItemName": ""},
            )
            fig_items.update_traces(
                hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
            )
            st.plotly_chart(_styled(fig_items), use_container_width=True)

    with col_right3:
        if "Buyer" in filtered.columns and "Category" in filtered.columns and "TotalCost" in filtered.columns:
            buyer_cat = filtered.pivot_table(
                index="Buyer", columns="Category", values="TotalCost", aggfunc="sum", fill_value=0
            )
            fig_heat = px.imshow(
                buyer_cat,
                color_continuous_scale=["#0F172A", "#7C3AED", "#F59E0B"],
                title="Buyer × Category Heatmap",
                labels=dict(x="Category", y="Buyer", color="Spend ($)"),
                aspect="auto",
            )
            fig_heat.update_traces(
                hovertemplate="<b>%{y}</b> – %{x}<br>$%{z:,.2f}<extra></extra>",
            )
            st.plotly_chart(_styled(fig_heat), use_container_width=True)

    with st.expander("View filtered transaction data", expanded=False):
        st.dataframe(
            filtered.sort_values("PurchaseDate", ascending=False) if "PurchaseDate" in filtered.columns else filtered,
            use_container_width=True,
            height=400,
        )
        st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
