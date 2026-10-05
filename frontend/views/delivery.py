import streamlit as st
from frontend.utils import api_get, api_put


def render_delivery_panel():
    user = st.session_state.get("user", {})
    user_role = user.get("role", "Delivery")
    delivery_user_id = user.get("user_id")

    st.markdown("## 🚚 Delivery Partner & Fleet Dashboard")
    st.caption(f"Logged in as: **{user.get('name', 'Driver')}** ({user_role})")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Refresh Queue", use_container_width=True):
            st.rerun()

    # Fetch orders based on role: Admin sees all fleet orders, Delivery sees active/ready orders
    if user_role == "Admin":
        orders, err = api_get("/admin/orders")
    else:
        orders, err = api_get("/delivery/orders", params={"delivery_user_id": delivery_user_id})

    if err:
        st.error(err)
        return

    if not orders:
        st.info("ℹ️ No active orders in delivery pipeline yet. Place an order as Customer, and mark it 'Ready' in Kitchen!")
        st.markdown("""
        <div style="background: #FFF8F0; padding: 16px; border-radius: 12px; border: 1px dashed #FFE0B2;">
            <h4 style="margin:0 0 8px 0; color: #E65100;">💡 How the Delivery Workflow Works:</h4>
            <ol style="margin:0; padding-left: 20px; color: #475569;">
                <li><b>Customer places an order</b> (Status = <i>Pending</i>).</li>
                <li><b>Kitchen starts cooking</b> (Status = <i>Preparing</i>) and marks it <b>'Ready'</b>.</li>
                <li>The order immediately appears here in the <b>'Ready for Pickup'</b> section!</li>
                <li>Delivery Boy clicks <b>'Pick Up'</b> ➔ Status = <i>Out for Delivery</i>.</li>
                <li>Delivery Boy verifies OTP PIN &amp; clicks <b>'Confirm Handover'</b> ➔ Status = <i>Delivered</i>!</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    ready_orders = [o for o in orders if o["status"] == "Ready"]
    active_orders = [o for o in orders if o["status"] == "Out for Delivery"]
    done_orders = [o for o in orders if o["status"] == "Delivered"]
    pending_prep_orders = [o for o in orders if o["status"] in ("Pending", "Preparing")]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🍳 In Kitchen", len(pending_prep_orders))
    c2.metric("📦 Ready for Pickup", len(ready_orders))
    c3.metric("🚚 On the Way", len(active_orders))
    c4.metric("✅ Delivered", len(done_orders))

    st.divider()

    # If no ready or active orders, show helpful guide
    if not ready_orders and not active_orders and not done_orders:
        st.info("ℹ️ Kitchen is currently preparing orders. Orders will move here as soon as Kitchen marks them 'Ready'!")

    # ── 1. READY FOR PICKUP ──
    if ready_orders:
        st.markdown("### 📦 Available Orders for Pickup")
        for order in ready_orders:
            oid = order["order_id"]
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Order #{oid}** 🟢 `Food Ready in Kitchen`")
                    st.write(f"👤 Customer: **{order.get('customer_name', 'Guest')}** · 📞 Phone: `{order.get('customer_phone', 'N/A')}`")
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
        with st.expander(f"✅ Completed Deliveries ({len(done_orders)})", expanded=False):
            for order in done_orders:
                st.write(f"Order #{order['order_id']} · ₹{float(order['total_amount']):.2f} · Customer: {order.get('customer_name', 'Guest')} · Rating: {'⭐' * int(order.get('rating') or 5)}")
