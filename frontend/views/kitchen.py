import streamlit as st
from frontend.utils import api_get, api_put


def render_kitchen_kds():
    st.markdown("## 🍳 Kitchen Display")

    if st.button("🔄 Refresh", use_container_width=False):
        st.rerun()

    # Kitchen only cares about: Pending, Preparing, Ready
    status_filter = st.radio(
        "Filter",
        ["Pending", "Preparing", "Ready", "All"],
        horizontal=True
    )

    params = {} if status_filter == "All" else {"status": status_filter}
    orders, err = api_get("/admin/orders", params=params)

    if err:
        st.error(err)
        return

    if not orders:
        st.info("No orders right now.")
        return

    # Count by status
    pending = sum(1 for o in orders if o["status"] == "Pending")
    preparing = sum(1 for o in orders if o["status"] == "Preparing")
    ready = sum(1 for o in orders if o["status"] == "Ready")

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Pending", pending)
    c2.metric("🟡 Preparing", preparing)
    c3.metric("🟢 Ready", ready)

    st.divider()

    for order in orders:
        oid = order["order_id"]
        status = order["status"]

        badge = {"Pending": "🔴", "Preparing": "🟡", "Ready": "🟢"}.get(status, "⚪")

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Order #{oid}** {badge} `{status}`")
                st.caption(f"{order.get('customer_name', 'Guest')} · {order.get('customer_phone', '')}")
                st.caption(f"📍 {order['delivery_address']}")
            with col2:
                st.markdown(f"**₹{float(order['total_amount']):.2f}**")

            # Items list
            for item in order.get("items", []):
                st.write(f"  • {item['name']} × {item['quantity']}")

            # Kitchen action buttons — proper workflow
            if status == "Pending":
                if st.button(f"🍳 Start Preparing", key=f"prep_{oid}", use_container_width=True):
                    api_put("/admin/orders/status", {"order_id": oid, "status": "Preparing"})
                    st.rerun()

            elif status == "Preparing":
                if st.button(f"✅ Mark Ready for Pickup", key=f"ready_{oid}", use_container_width=True):
                    api_put("/admin/orders/status", {"order_id": oid, "status": "Ready"})
                    st.rerun()

            elif status == "Ready":
                st.success("✅ Waiting for Delivery Boy to pick up")

            # Cancel option for any active order
            if status in ("Pending", "Preparing"):
                if st.button(f"❌ Cancel", key=f"cancel_{oid}"):
                    api_put("/admin/orders/status", {"order_id": oid, "status": "Cancelled"})
                    st.rerun()
