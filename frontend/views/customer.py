import streamlit as st
from frontend.utils import api_get, api_post, api_put


def render_customer_portal():
    user = st.session_state.get("user", {})
    user_id = user.get("user_id", 1)

    # ─── HERO BANNER ───
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #FF5722 0%, #E64A19 50%, #D84315 100%);
        padding: 32px 38px;
        border-radius: 24px;
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 12px 35px rgba(230, 81, 0, 0.28);
        position: relative;
        overflow: hidden;
    ">
        <div style="position: relative; z-index: 2;">
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
                <span style="background: rgba(255,255,255,0.25); backdrop-filter: blur(4px); padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;">⚡ FAST 30-MIN EXPRESS DELIVERY</span>
                <span style="background: rgba(255,255,255,0.25); backdrop-filter: blur(4px); padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 700;">🌟 4.9 ★ GOURMET CHEFS</span>
                <span style="background: rgba(255,255,255,0.25); backdrop-filter: blur(4px); padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 700;">🔥 100% FRESH &amp; HYGIENIC</span>
            </div>
            <h1 style="margin: 0; font-size: 36px; font-weight: 800; color: #FFFFFF !important; line-height: 1.2;">
                Craving Something Delicious Today? 🍕✨
            </h1>
            <p style="margin: 12px 0 0 0; font-size: 16px; color: #FFE0B2 !important; font-weight: 500;">
                Order authentic chef-prepared delicacies with real-time live tracking &amp; instant UPI payment!
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🔥 Explore Gourmet Menu", "🛒 Cart & Checkout", "📍 Live Order Tracking"])

    # ─── TAB 1: ANIMATED FOOD SHOWCASE ───
    with tabs[0]:
        categories_data, _ = api_get("/categories")
        category_options = ["All Categories"]
        if categories_data:
            category_options += [c["name"] for c in categories_data]

        col_f, col_s = st.columns([1, 2])
        with col_f:
            selected_cat = st.selectbox("📂 Filter by Category", category_options)
        with col_s:
            search = st.text_input("🔍 Search Dish or Ingredient", placeholder="Search Paneer, Butter Chicken, Lassi...")

        cat_filter_name = None if selected_cat == "All Categories" else selected_cat
        params = {} if not cat_filter_name else {"category": cat_filter_name}
        items, err = api_get("/menu", params=params)

        if err:
            st.error(err)
            return
        if not items:
            st.info("No delicious food items found matching your filter.")
            return

        if search:
            items = [
                i for i in items
                if search.lower() in i["name"].lower() or search.lower() in (i["description"] or "").lower()
            ]

        st.caption(f"Showing **{len(items)}** gourmet dishes available right now:")

        # Grid view
        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                with st.container(border=True):
                    item_id = item["item_id"]
                    img = item.get("image_url") or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"
                    cat_name = item.get("category_name", "Special")
                    avail = item.get("is_available", True)
                    price = float(item["price"])

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="background: linear-gradient(135deg, #FFF3E0, #FFE0B2); color: #E65100; padding: 4px 12px; border-radius: 14px; font-size: 12px; font-weight: 800; border: 1px solid #FFE0B2;">
                            🏷️ {cat_name}
                        </span>
                        <span style="font-size: 12px; font-weight: 800; color: {'#166534' if avail else '#991B1B'}; background: {'#DCFCE7' if avail else '#FEE2E2'}; padding: 4px 10px; border-radius: 12px;">
                            {'🟢 In Stock' if avail else '🔴 Sold Out'}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.image(img, use_container_width=True)

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-top: 8px;">
                        <div>
                            <h3 style="margin:0; font-size: 19px; font-weight: 800; color: #0F172A;">{item['name']}</h3>
                            <span style="font-size: 12px; color: #F59E0B; font-weight: 700;">★ 4.8 (120+ orders)</span>
                        </div>
                        <div style="background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%); color: white; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 16px; box-shadow: 0 4px 12px rgba(255, 87, 34, 0.25);">
                            ₹{price:.0f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    desc = item.get("description") or "Chef's special freshly prepared delicious dish."
                    st.markdown(f"<p style='color: #64748B; font-size: 13px; margin: 8px 0 12px 0; min-height: 38px;'>{desc[:110] + ('...' if len(desc) > 110 else '')}</p>", unsafe_allow_html=True)

                    if avail:
                        qty = st.session_state.cart.get(item_id, {}).get("qty", 0)

                        if qty == 0:
                            if st.button("🛒 Add to Order", key=f"add_{item_id}", use_container_width=True, type="primary"):
                                st.session_state.cart[item_id] = {
                                    "item_id": item_id,
                                    "name": item["name"],
                                    "price": price,
                                    "qty": 1
                                }
                                st.toast(f"Added {item['name']} to cart! 😋")
                                st.rerun()
                        else:
                            c_minus, c_qty, c_plus = st.columns([1, 1.2, 1])
                            with c_minus:
                                if st.button("−", key=f"m_{item_id}", use_container_width=True):
                                    if qty > 1:
                                        st.session_state.cart[item_id]["qty"] -= 1
                                    else:
                                        del st.session_state.cart[item_id]
                                    st.rerun()
                            with c_qty:
                                st.markdown(f"<div style='text-align:center; padding-top:6px; font-weight:800; font-size:16px; color:#E65100;'>{qty} in Cart</div>", unsafe_allow_html=True)
                            with c_plus:
                                if st.button("+", key=f"p_{item_id}", use_container_width=True):
                                    st.session_state.cart[item_id]["qty"] += 1
                                    st.rerun()
                    else:
                        st.button("🚫 Out of Stock", key=f"disabled_{item_id}", disabled=True, use_container_width=True)

    # ─── TAB 2: CART & CHECKOUT ───
    with tabs[1]:
        if not st.session_state.cart:
            st.info("🛒 Your cart is currently empty! Explore the Food Showcase above to add your favorite dishes.")
        else:
            st.subheader("🛒 Your Order Summary")
            cart_items = list(st.session_state.cart.values())

            for item in cart_items:
                c1, c2, c3, c4 = st.columns([3, 1, 1.5, 1])
                with c1:
                    st.markdown(f"**{item['name']}**")
                    st.caption(f"₹{item['price']:.2f} per item")
                with c2:
                    st.markdown(f"**Qty: {item['qty']}**")
                with c3:
                    sub_total = item['price'] * item['qty']
                    st.markdown(f"**₹{sub_total:.2f}**")
                with c4:
                    if st.button("🗑️", key=f"del_{item['item_id']}"):
                        del st.session_state.cart[item['item_id']]
                        st.toast(f"Removed {item['name']} from cart.")
                        st.rerun()

            st.divider()

            subtotal = sum(i['price'] * i['qty'] for i in cart_items)
            gst = subtotal * 0.05
            total = subtotal + gst

            col_bill, col_pay = st.columns(2)
            with col_bill:
                with st.container(border=True):
                    st.markdown("### 🧾 Payment Breakdown")
                    st.write(f"Item Subtotal: **₹{subtotal:.2f}**")
                    st.write(f"GST & Taxes (5%): **₹{gst:.2f}**")
                    st.write(f"Delivery Fee: **FREE ⚡**")
                    st.markdown(f"## Total Amount: ₹{total:.2f}")

            with col_pay:
                st.markdown("### 📦 Delivery Details")
                address = st.text_area("📍 House / Office Address", placeholder="Enter house number, building name, street address...")
                pay_method = st.radio("💳 Choose Payment Method", ["UPI (GPay / PhonePe / Paytm)", "Cash on Delivery (COD)", "Credit / Debit Card"], horizontal=False)

                upi_id = ""
                if "UPI" in pay_method:
                    upi_id = st.text_input("📲 Enter UPI VPA ID", value="customer@okaxis", placeholder="yourname@upi")

                if st.button("🚀 Confirm & Place Order Now", type="primary", use_container_width=True):
                    if not address.strip():
                        st.error("Please enter your complete delivery address.")
                    else:
                        method = "UPI" if "UPI" in pay_method else ("Card" if "Card" in pay_method else "COD")
                        payload = {
                            "user_id": user_id,
                            "address": address.strip(),
                            "items": [{"item_id": i["item_id"], "qty": i["qty"], "price": i["price"]} for i in cart_items],
                            "payment_method": method
                        }

                        res, err = api_post("/orders", payload)
                        if err:
                            st.error(err)
                        else:
                            order_id = res.get("order_id")

                            if method == "UPI" and upi_id:
                                upi_res, _ = api_post("/payments/upi/initiate", {
                                    "order_id": order_id, "upi_id": upi_id, "amount": total
                                })
                                if upi_res:
                                    tx_id = upi_res["payment"]["transaction_id"]
                                    api_post("/payments/verify", {
                                        "order_id": order_id, "transaction_id": tx_id, "status": "Completed"
                                    })

                            st.session_state.tracked_order_id = order_id
                            st.session_state.cart = {}
                            st.balloons()
                            st.success(f"🎉 Order #{order_id} placed successfully! You can track live updates in 'Live Order Tracking'.")

    # ─── TAB 3: LIVE TRACKING & CUSTOMER INTERACTION ───
    with tabs[2]:
        st.subheader("📍 Live Order Tracking & Customer Handover Interaction")

        orders, err = api_get(f"/orders/user/{user_id}")
        if err:
            st.error(err)
            return

        if not orders:
            st.info("You haven't placed any orders yet.")
            return

        for order in orders:
            oid = order["order_id"]
            status = order.get("status", "Pending")
            otp = order.get("otp_code", "1234")
            rating = order.get("rating")
            review = order.get("review_text", "")

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### Order #{oid}")
                    st.caption(f"🕒 Placed on {order.get('created_at', 'Recently')} · Payment: **{order.get('payment_method', 'COD')}** ({order.get('payment_status', 'Pending')})")
                    st.write(f"📍 **Address:** {order.get('delivery_address', 'N/A')}")
                with col2:
                    st.markdown(f"<h3 style='color:#E65100; margin:0;'>₹{float(order['total_amount']):.2f}</h3>", unsafe_allow_html=True)

                st.markdown("**Dishes Ordered:**")
                for itm in order.get("items", []):
                    st.write(f"• **{itm['name']}** × {itm['quantity']} @ ₹{float(itm['unit_price']):.2f} each")

                st.divider()

                # ── 5-STEP VISUAL TRACKER ──
                all_steps = ["Pending", "Preparing", "Ready", "Out for Delivery", "Delivered"]

                if status == "Cancelled":
                    st.error("❌ This order was cancelled.")
                else:
                    current_idx = all_steps.index(status) if status in all_steps else 0
                    st.progress((current_idx + 1) / len(all_steps))

                    step_cols = st.columns(5)
                    icons = ["🔴", "🍳", "📦", "🚚", "✅"]
                    labels = ["Order Placed", "Preparing", "Food Ready", "On The Way", "Delivered"]

                    for i, step in enumerate(all_steps):
                        with step_cols[i]:
                            if i <= current_idx:
                                st.markdown(f"<div style='text-align:center; color:#E65100; font-weight:700;'>{icons[i]}<br>{labels[i]}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='text-align:center; color:#94A3B8;'>⚪<br>{labels[i]}</div>", unsafe_allow_html=True)

                # ── INTERACTION: OUT FOR DELIVERY HANDOVER & OTP ──
                if status == "Out for Delivery":
                    st.warning(f"🔑 **Delivery Verification OTP:** `{otp}` (Share this 4-digit PIN with your delivery partner on arrival!)")
                    if order.get("delivery_boy_name"):
                        st.info(f"🛵 **Delivery Partner Assigned:** {order['delivery_boy_name']} (📞 {order.get('delivery_boy_phone', '9900112233')})")

                # ── INTERACTION: DELIVERED CONFIRMATION & RATING ──
                elif status == "Delivered":
                    st.success("🎉 **Food Delivered Successfully!** We hope you enjoy your meal.")
                    
                    if rating:
                        st.markdown(f"⭐ **Your Rating:** {'★' * rating}{'☆' * (5 - rating)} (`{rating}/5 Stars`)")
                        if review:
                            st.caption(f"💬 *\"{review}\"*")
                    else:
                        with st.expander("⭐ Rate & Review Your Delivery Experience", expanded=True):
                            with st.form(key=f"rate_form_{oid}"):
                                user_rating = st.slider("Select Rating (1 = Poor, 5 = Excellent)", 1, 5, 5)
                                user_review = st.text_input("Feedback Review (Optional)", placeholder="e.g. Delicious food, hot delivery!")
                                rate_sub = st.form_submit_button("Submit Rating & Review", type="primary")

                                if rate_sub:
                                    res, err = api_put(f"/orders/{oid}/rate", {
                                        "rating": user_rating,
                                        "review_text": user_review.strip()
                                    })
                                    if err:
                                        st.error(err)
                                    else:
                                        st.toast("Thank you for your rating & feedback! ❤️")
                                        st.rerun()
