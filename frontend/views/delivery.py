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
    st.markdown("## 🚚 Delivery Partner Dashboard")
    st.caption(f"Active Delivery Partner: **{user.get('name', 'Driver')}** ({user.get('email')})")

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Refresh Orders", use_container_width=True):
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
    c1.metric("🛵 Active Deliveries (On The Way)", len(assigned_active))
    c2.metric("✅ Completed Today", len(assigned_done))

    st.divider()

    if not assigned_active and not assigned_done:
        st.info(f"💡 **Hello {user.get('name', 'Driver')}!** You have no assigned deliveries right now.")
        st.markdown("""
        <div style="background:#FFF3E0; padding:18px; border-radius:14px; border:1px solid #FFE0B2; margin-top:10px;">
            <h4 style="margin:0 0 10px 0; color:#E65100;">🛵 Real-World Delivery Partner Workflow:</h4>
            <ol style="margin:0; padding-left:22px; color:#475569; line-height:1.7;">
                <li>Customer orders food on Food Express.</li>
                <li>Kitchen cooks and prepares the meal (Status: 🟢 <b>Ready</b>).</li>
                <li><b>Admin assigns the ready parcel specifically to YOU</b>.</li>
                <li>The order immediately pops up here with Customer Address, Phone, &amp; Navigation details.</li>
                <li>Reach Customer location, <b>ask Customer for 4-digit OTP</b>, enter it below to confirm delivery!</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── ASSIGNED ACTIVE DELIVERIES ──
    if assigned_active:
        st.markdown("### 🛵 Current Live Deliveries (Pending Handover)")
        for order in assigned_active:
            oid = order["order_id"]

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### 📦 Order #{oid} · 🔵 `Out for Delivery`")
                    st.markdown(f"**Customer:** {order.get('customer_name', 'Guest')}")
                    st.markdown(f"📞 **Customer Phone:** `{order.get('customer_phone', 'N/A')}`")
                    st.markdown(f"📍 **Delivery Address:** **{order['delivery_address']}**")
                with col2:
                    st.markdown(f"<h3 style='color:#E65100; margin:0;'>₹{float(order['total_amount']):.2f}</h3>", unsafe_allow_html=True)
                    st.caption(f"Payment Mode: **{order.get('payment_method', 'COD')}**")
                    st.caption(f"Payment Status: **{order.get('payment_status', 'Pending')}**")

                st.markdown("**Dishes in Parcel:**")
                for item in order.get("items", []):
                    st.caption(f"  • {item['name']} × {item['quantity']}")

                st.markdown("---")
                # Real-world Customer OTP Verification Form
                st.markdown("#### 🔐 Customer Handover Verification")
                st.caption("Ask customer for the 4-digit OTP shown on their tracking screen before handing over the food.")
                
                c_otp_in, c_otp_btn = st.columns([2, 1])
                with c_otp_in:
                    input_otp = st.text_input(f"Enter Customer OTP for Order #{oid}", max_chars=4, placeholder="e.g. 1234", key=f"otp_in_{oid}")
                with c_otp_btn:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button(f"✅ Verify OTP & Deliver #{oid}", key=f"delivered_{oid}", use_container_width=True, type="primary"):
                        if not input_otp or len(input_otp.strip()) != 4:
                            st.error("Please enter a valid 4-digit Customer OTP.")
                        else:
                            res, err = api_put("/delivery/delivered", {
                                "order_id": oid,
                                "entered_otp": input_otp.strip()
                            })
                            if err:
                                st.error(err)
                            else:
                                st.balloons()
                                st.success(f"Order #{oid} verified and delivered successfully! 🎉")
                                st.rerun()

    # ── COMPLETED BY THIS DRIVER ──
    if assigned_done:
        with st.expander(f"✅ Your Completed Deliveries Today ({len(assigned_done)})", expanded=False):
            for order in assigned_done:
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**Order #{order['order_id']}** (Delivered)")
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
