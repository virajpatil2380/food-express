import streamlit as st
from frontend.utils import api_get, api_put


def render_delivery_panel():
    user = st.session_state.get("user", {})
    delivery_user_id = user.get("user_id")

    st.markdown("## 🚚 Delivery Dashboard")
    st.caption(f"Delivery Partner: **{user.get('name', 'Driver')}**")

    if st.button("🔄 Refresh Orders", use_container_width=False):
        st.rerun()

    orders, err = api_get("/delivery/orders", params={"delivery_user_id": delivery_user_id})

    if err:
        st.error(err)
        return

    if not orders:
        st.info("No orders to deliver right now. Check back soon!")
        return

    # Split orders by status
    ready_orders = [o for o in orders if o["status"] == "Ready"]
    active_orders = [o for o in orders if o["status"] == "Out for Delivery"]
    done_orders = [o for o in orders if o["status"] == "Delivered"]

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Ready for Pickup", len(ready_orders))
    c2.metric("🚚 On the Way", len(active_orders))
    c3.metric("✅ Delivered Today", len(done_orders))

    st.divider()

    # ── READY FOR PICKUP ──
    if ready_orders:
        st.markdown("### 📦 Ready for Pickup")
        for order in ready_orders:
            oid = order["order_id"]
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Order #{oid}** 🟢 `Ready`")
                    st.write(f"👤 {order.get('customer_name', 'Guest')} · 📞 {order.get('customer_phone', 'N/A')}")
                    st.write(f"📍 {order['delivery_address']}")
                with col2:
                    st.markdown(f"**₹{float(order['total_amount']):.2f}**")
                    st.caption(f"💳 {order.get('payment_method', 'COD')}")

                for item in order.get("items", []):
                    st.caption(f"  • {item['name']} × {item['quantity']}")

                if st.button(f"🚚 Pick Up Order #{oid}", key=f"pickup_{oid}", use_container_width=True, type="primary"):
                    api_put("/delivery/pickup", {
                        "order_id": oid,
                        "delivery_user_id": delivery_user_id
                    })
                    st.success(f"Order #{oid} picked up! Drive safe 🚗")
                    st.rerun()

    # ── OUT FOR DELIVERY ──
    if active_orders:
        st.markdown("### 🚚 Out for Delivery")
        for order in active_orders:
            oid = order["order_id"]
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Order #{oid}** 🔵 `Out for Delivery`")
                    st.write(f"👤 {order.get('customer_name', 'Guest')} · 📞 {order.get('customer_phone', 'N/A')}")
                    st.write(f"📍 **{order['delivery_address']}**")
                with col2:
                    st.markdown(f"**₹{float(order['total_amount']):.2f}**")

                if st.button(f"✅ Mark Delivered #{oid}", key=f"delivered_{oid}", use_container_width=True, type="primary"):
                    api_put("/delivery/delivered", {"order_id": oid})
                    st.balloons()
                    st.success(f"Order #{oid} delivered! 🎉")
                    st.rerun()

    # ── COMPLETED ──
    if done_orders:
        with st.expander(f"✅ Completed Deliveries ({len(done_orders)})", expanded=False):
            for order in done_orders:
                st.write(f"Order #{order['order_id']} · ₹{float(order['total_amount']):.2f} · {order.get('customer_name', 'Guest')}")
