import streamlit as st
from frontend.utils import api_get, api_put


def render_delivery_panel():
    user = st.session_state.get("user", {})
    delivery_user_id = user.get("user_id")

    st.markdown("## 🚚 Delivery Partner & Logistics Panel")
    st.caption(f"Logistics View | Active Account: **{user.get('name', 'Driver')}** ({user.get('role', 'Delivery')})")

    if st.button("🔄 Refresh Delivery Queue", use_container_width=False):
        st.rerun()

    orders, err = api_get("/delivery/orders", params={"delivery_user_id": delivery_user_id})

    if err:
        st.error(err)
        return

    ready_orders = [o for o in orders if o["status"] == "Ready"] if orders else []
    active_orders = [o for o in orders if o["status"] == "Out for Delivery"] if orders else []
    done_orders = [o for o in orders if o["status"] == "Delivered"] if orders else []

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Ready for Pickup", len(ready_orders))
    c2.metric("🚚 On the Way", len(active_orders))
    c3.metric("✅ Delivered History", len(done_orders))

    st.divider()

    if not orders or (not ready_orders and not active_orders and not done_orders):
        st.info("💡 **Delivery Queue Status:** No active orders in `Ready` or `Out for Delivery` state.")
        st.markdown("""
        <div style="background:#FFF3E0; padding:16px; border-radius:12px; border:1px solid #FFE0B2; margin-top:10px;">
            <h4 style="margin:0 0 8px 0; color:#E65100;">ℹ️ How Delivery Queue Works:</h4>
            <ol style="margin:0; padding-left:20px; color:#555;">
                <li><b>Customer</b> places an order (Status: 🔴 <i>Pending</i>).</li>
                <li><b>Kitchen</b> cooks the food and clicks <b>'Mark Ready for Pickup'</b> (Status: 🟢 <i>Ready</i>).</li>
                <li>The moment Kitchen marks it Ready, the order automatically appears right here for pickup!</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 1. READY FOR PICKUP ──
    if ready_orders:
        st.markdown("### 📦 Available Orders for Pickup")
        for order in ready_orders:
            oid = order["order_id"]
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### Order #{oid} 🟢 `Food Ready in Kitchen`")
                    st.write(f"👤 Customer: **{order.get('customer_name', 'Guest')}** · 📞 Call: `{order.get('customer_phone', 'N/A')}`")
                    st.write(f"📍 **Address:** {order['delivery_address']}")
                with col2:
                    st.markdown(f"**₹{float(order['total_amount']):.2f}**")
                    st.caption(f"Payment: `{order.get('payment_method', 'COD')}`")

                st.markdown("**Dishes to Deliver:**")
                for item in order.get("items", []):
                    st.caption(f"  • {item['name']} × {item['quantity']}")

                if st.button(f"🚚 Pick Up Order #{oid}", key=f"pickup_{oid}", use_container_width=True, type="primary"):
                    api_put("/delivery/pickup", {
                        "order_id": oid,
                        "delivery_user_id": delivery_user_id
                    })
                    st.success(f"Order #{oid} picked up! Customer notified. 🚗")
                    st.rerun()

    # ── 2. OUT FOR DELIVERY & CUSTOMER HANDOVER ──
    if active_orders:
        st.markdown("### 🚚 On The Way (Active Deliveries)")
        for order in active_orders:
            oid = order["order_id"]
            otp = order.get("otp_code", "1234")

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### Order #{oid} 🔵 `Out for Delivery`")
                    st.write(f"👤 Customer: **{order.get('customer_name', 'Guest')}** · 📞 Call: `{order.get('customer_phone', 'N/A')}`")
                    st.write(f"📍 **Delivery Address:** {order['delivery_address']}")
                    st.info(f"🔑 **Customer OTP Verification PIN:** `{otp}`")
                with col2:
                    st.markdown(f"<h3 style='color:#E65100; margin:0;'>₹{float(order['total_amount']):.2f}</h3>", unsafe_allow_html=True)
                    st.caption(f"Method: **{order.get('payment_method', 'COD')}**")

                if st.button(f"✅ Verify OTP & Confirm Handover #{oid}", key=f"delivered_{oid}", use_container_width=True, type="primary"):
                    api_put("/delivery/delivered", {"order_id": oid})
                    st.balloons()
                    st.success(f"Order #{oid} delivered successfully! Customer can now rate their experience. 🎉")
                    st.rerun()

    # ── 3. COMPLETED DELIVERIES ──
    if done_orders:
        with st.expander(f"✅ Completed Deliveries ({len(done_orders)})", expanded=True):
            for order in done_orders:
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**Order #{order['order_id']}**")
                c2.write(f"Customer: {order.get('customer_name', 'Guest')} ({order.get('customer_phone', 'N/A')})")
                c3.write(f"**₹{float(order['total_amount']):.2f}**")
