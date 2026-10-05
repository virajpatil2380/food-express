import streamlit as st
import pandas as pd
from frontend.utils import api_get

def render_analytics_dashboard():
    st.title("📊 Business Owner Analytics")
    st.caption("Revenue trends, operational KPIs, and product performance insights.")

    analytics_data, err = api_get("/admin/analytics")

    if err:
        st.error(err)
        return

    if not analytics_data:
        st.info("No analytics data available yet.")
        return

    # --- FR-3.1: KPI SCORECARDS ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"₹{analytics_data.get('total_revenue', 0):,.2f}"
        )
    with col2:
        st.metric(
            label="📦 Total Orders",
            value=f"{analytics_data.get('total_orders', 0)}"
        )
    with col3:
        st.metric(
            label="🎯 Average Order Value (AOV)",
            value=f"₹{analytics_data.get('aov', 0):,.2f}"
        )

    st.divider()

    # --- FR-3.2: VISUAL ANALYTICS ---
    col_chart1, col_chart2 = st.columns(2)

    # 1. Revenue Trend Line Chart
    with col_chart1:
        st.markdown("### 📈 Revenue Trend Over Time")
        trend_raw = analytics_data.get("revenue_trend", [])
        if trend_raw:
            df_trend = pd.DataFrame(trend_raw)
            df_trend["daily_revenue"] = df_trend["daily_revenue"].astype(float)
            df_trend["order_date"] = pd.to_datetime(df_trend["order_date"])
            df_trend = df_trend.set_index("order_date")
            st.line_chart(df_trend[["daily_revenue"]], height=300)
        else:
            st.info("No revenue history available to plot trend chart.")

    # 2. Top-Selling Items Bar Chart
    with col_chart2:
        st.markdown("### 🏆 Top Selling Items")
        top_raw = analytics_data.get("top_items", [])
        if top_raw:
            df_top = pd.DataFrame(top_raw)
            df_top["total_qty"] = df_top["total_qty"].astype(int)
            df_top_chart = df_top.set_index("name")[["total_qty"]]
            st.bar_chart(df_top_chart, height=300)
        else:
            st.info("No sales data available for item ranking.")

    # Detailed Table Breakdown
    st.divider()
    st.markdown("### 📄 Sales Breakdown by Item")
    if top_raw:
        df_display = pd.DataFrame(top_raw)
        df_display.columns = ["Item Name", "Quantity Sold", "Total Revenue (₹)"]
        df_display["Total Revenue (₹)"] = df_display["Total Revenue (₹)"].astype(float).map("₹{:,.2f}".format)
        st.dataframe(df_display, use_container_width=True)
