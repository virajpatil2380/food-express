import streamlit as st
from frontend.utils import api_get, api_put


def render_delivery_panel():
    user = st.session_state.get("user", {})
    user_role = user.get("role", "Customer")
    delivery_user_id = user.get("user_id")

    # If Admin is inspecting, render Admin Dispatch Management View
    if user_role == "Admin":
        render_admin_delivery_dispatch()
        return

    # ─── DEDICATED DELIVERY PARTNER DASHBOARD ───
    st.markdown("## 🚚 My Delivery Assignments")
    st.caption(f"Logged in as Delivery Partner: **{user.get('name', 'Driver')}** ({user.get('email')})")

    if st.button("🔄 Refresh My Delivery Queue", use_container_width=False):
        st.rerun()

    # Fetch ONLY orders assigned to THIS specific delivery partner
    orders, err = api_get("/delivery/orders", params={"delivery_user_id": delivery_user_id})

    if err:
        st.error(err)
        return

    # Filter strictly for assigned orders to this user_id
    assigned_active = [o for o in orders if o["status"] == "Out for Delivery" and o.get("delivery_user_id") == delivery_user_id] if orders else []
    assigned_done = [o for o in orders if o["status"] == "Delivered" and o.get("delivery_user_id") == delivery_user_id] if orders else []

    c1, c2 = st.columns(2)
    c1.metric("🚚 Assigned On The Way", len(assigned_active))
    c2.metric("✅ Delivered By Me Today", len(assigned_done))

    st.divider()

    if not assigned_active and not assigned_done:
        st.info(f"💡 **Hello {user.get('name', 'Driver')}!** You have 0 assigned deliveries in your queue.")
        st.markdown("""
        <div style="background:#FFF3E0; padding:16px; border-radius:12px; border:1px solid #FFE0B2; margin-top:10px;">
            <h4 style="margin:0 0 8px 0; color:#E65100;">ℹ️ How Delivery Assignment Works:</h4>
            <ol style="margin:0; padding-left:20px; color:#555;">
                <li>Customer places an order ➔ Kitchen cooks &amp; marks order 🟢 <b>Ready</b>.</li>
                <li><b>Admin</b> assigns the ready order specifically to <b>YOUR account</b>.</li>
                <li>The moment Admin assigns an order to you, it will appear right here with Customer Address, Phone, &amp; Verification OTP!</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── ASSIGNED ACTIVE DELIVERIES ──
    if assigned_active:
        st.markdown("### 🚚 Assigned Active Deliveries")
        for order in assigned_active:
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

                st.markdown("**Dishes to Deliver:**")
                for item in order.get("items", []):
                    st.caption(f"  • {item['name']} × {item['quantity']}")

                if st.button(f"✅ Verify OTP & Complete Handover #{oid}", key=f"delivered_{oid}", use_container_width=True, type="primary"):
                    api_put("/delivery/delivered", {"order_id": oid})
                    st.balloons()
                    st.success(f"Order #{oid} delivered successfully! 🎉")
                    st.rerun()

    # ── COMPLETED BY THIS DRIVER ──
    if assigned_done:
        with st.expander(f"✅ Completed Deliveries ({len(assigned_done)})", expanded=True):
            for order in assigned_done:
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**Order #{order['order_id']}**")
                c2.write(f"Customer: {order.get('customer_name', 'Guest')} ({order.get('customer_phone', 'N/A')})")
                c3.write(f"**₹{float(order['total_amount']):.2f}**")


def render_admin_delivery_dispatch():
    """Admin View: Assigns Ready orders to specific registered Delivery Partners."""
    st.markdown("## 👑 Admin Delivery Dispatch Control")
    st.caption("Assign ready kitchen orders to specific Delivery Partners.")

    if st.button("🔄 Refresh Dispatch Status", use_container_width=False):
        st.rerun()

    # Fetch all orders & delivery partners
    orders, err1 = api_get("/delivery/orders")
    partners, err2 = api_get("/admin/delivery_partners")

    if err1:
        st.error(err1)
        return

    partner_map = {f"{p['name']} ({p['email']})": p["user_id"] for p in partners} if partners else {}

    ready_orders = [o for o in orders if o["status"] == "Ready"] if orders else []
    active_orders = [o for o in orders if o["status"] == "Out for Delivery"] if orders else []
    done_orders = [o for o in orders if o["status"] == "Delivered"] if orders else []

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Unassigned (Ready)", len(ready_orders))
    c2.metric("🚚 Assigned (On The Way)", len(active_orders))
    c3.metric("✅ Total Delivered", len(done_orders))

    st.divider()

    # ── UNASSIGNED READY ORDERS ──
    st.markdown("### 🎯 Assign Delivery Partner to Ready Orders")
    if not ready_orders:
        st.info("No unassigned 'Ready' orders right now. Orders marked 'Ready' by Kitchen will appear here for assignment.")
    else:
        for order in ready_orders:
            oid = order["order_id"]
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Order #{oid}** 🟢 `Ready in Kitchen`")
                    st.write(f"Customer: **{order.get('customer_name', 'Guest')}** ({order.get('customer_phone', 'N/A')})")
                    st.write(f"📍 Address: {order['delivery_address']}")
                    st.write(f"Total: **₹{float(order['total_amount']):.2f}**")
                with col2:
                    st.markdown("**Assign Partner:**")
                    if partner_map:
                        selected_partner_label = st.selectbox(
                            "Select Delivery Boy",
                            list(partner_map.keys()),
                            key=f"partner_select_{oid}"
                        )
                        target_user_id = partner_map[selected_partner_label]

                        if st.button(f"🎯 Assign to Driver", key=f"assign_btn_{oid}", type="primary", use_container_width=True):
                            api_put("/admin/orders/assign_delivery", {
                                "order_id": oid,
                                "delivery_user_id": target_user_id
                            })
                            st.success(f"Assigned Order #{oid} to {selected_partner_label}!")
                            st.rerun()
                    else:
                        st.warning("No Delivery Partners registered yet.")

    # ── ACTIVE DELIVERIES ──
    if active_orders:
        st.divider()
        st.markdown("### 🚚 Currently Assigned Active Deliveries")
        for order in active_orders:
            oid = order["order_id"]
            st.write(f"• **Order #{oid}** ➔ Assigned to: **{order.get('delivery_boy_name', 'Driver')}** ({order.get('delivery_boy_phone', '')}) | Address: {order.get('delivery_address')}")
