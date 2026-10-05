import streamlit as st
from frontend.utils import api_get, api_post, api_put, api_delete


def render_menu_management():
    st.title("📦 Menu & Inventory Control")
    st.caption("Full product management — Add, Edit, Delete dishes and control stock availability.")

    # Initialize edit state
    if "editing_item" not in st.session_state:
        st.session_state.editing_item = None

    # ──────────────────────────────────────────
    # TOP SECTION: Add New Item / Edit Item Form
    # ──────────────────────────────────────────
    categories, _ = api_get("/categories")
    category_map = {c["name"]: c["category_id"] for c in categories} if categories else {}
    category_names = list(category_map.keys()) if category_map else ["Starters"]

    editing = st.session_state.editing_item

    if editing:
        _render_edit_form(editing, category_names, category_map)
    else:
        _render_add_form(category_names, category_map)

    st.divider()

    # ──────────────────────────────────────────
    # BOTTOM SECTION: All Menu Items with Actions
    # ──────────────────────────────────────────
    st.markdown("### 📋 All Menu Items")

    menu_items, err = api_get("/menu")
    if err:
        st.error(err)
        return
    if not menu_items:
        st.info("No menu items yet. Add your first dish above!")
        return

    st.caption(f"Total: **{len(menu_items)} items** in menu")

    for item in menu_items:
        item_id = item["item_id"]
        is_avail = bool(item["is_available"])

        with st.container(border=True):
            img_col, details_col, actions_col = st.columns([1, 3, 2])

            with img_col:
                img_src = item.get("image_url") or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"
                st.image(img_src, use_container_width=True)

            with details_col:
                st.markdown(f"**{item['name']}**")
                st.write(f"₹{float(item['price']):.2f} · {item.get('category_name', 'General')}")
                desc = item.get("description") or "No description"
                st.caption(desc[:120] + ("..." if len(desc) > 120 else ""))

            with actions_col:
                # Stock Status Badge
                if is_avail:
                    st.success("🟢 In Stock", icon="✅")
                else:
                    st.error("🔴 Out of Stock", icon="❌")

                # Action Buttons Row
                btn_edit, btn_stock, btn_del = st.columns(3)

                with btn_edit:
                    if st.button("✏️ Edit", key=f"edit_{item_id}", use_container_width=True):
                        st.session_state.editing_item = item
                        st.rerun()

                with btn_stock:
                    new_label = "❌ Hide" if is_avail else "✅ Show"
                    if st.button(new_label, key=f"stock_{item_id}", use_container_width=True):
                        api_put(f"/admin/menu/{item_id}/availability", {"is_available": not is_avail})
                        st.rerun()

                with btn_del:
                    if st.button("🗑️ Del", key=f"del_{item_id}", use_container_width=True):
                        st.session_state[f"confirm_del_{item_id}"] = True
                        st.rerun()

                # Delete Confirmation
                if st.session_state.get(f"confirm_del_{item_id}"):
                    st.warning(f"⚠️ Delete **{item['name']}** permanently?")
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("Yes, Delete", key=f"yes_del_{item_id}", type="primary", use_container_width=True):
                            res, err = api_delete(f"/admin/menu/{item_id}")
                            if err:
                                st.error(err)
                            else:
                                st.toast(f"🗑️ Deleted {item['name']}")
                                del st.session_state[f"confirm_del_{item_id}"]
                                st.rerun()
                    with c_no:
                        if st.button("Cancel", key=f"no_del_{item_id}", use_container_width=True):
                            del st.session_state[f"confirm_del_{item_id}"]
                            st.rerun()


def _render_add_form(category_names, category_map):
    """Form to add a new dish to the menu."""
    with st.form("add_item_form", clear_on_submit=True):
        st.markdown("### ➕ Add New Dish")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Dish Name *", placeholder="e.g. Garlic Cheese Bread")
            category_name = st.selectbox("Category *", category_names)
        with col2:
            price = st.number_input("Price (₹) *", min_value=1.0, value=150.0, step=10.0)
            image_url = st.text_input("Image URL", placeholder="https://images.unsplash.com/photo-...")

        description = st.text_area("Description", placeholder="Ingredients, taste notes, or preparation details...", height=80)

        submitted = st.form_submit_button("💾 Save Dish", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Dish name is required.")
            else:
                payload = {
                    "name": name.strip(),
                    "price": price,
                    "category_id": category_map.get(category_name, 1),
                    "description": description.strip(),
                    "image_url": image_url.strip()
                }
                res, err = api_post("/admin/menu", payload)
                if err:
                    st.error(err)
                else:
                    st.success(f"✅ Added **{name}** to menu!")
                    st.rerun()


def _render_edit_form(item, category_names, category_map):
    """Form to edit an existing dish."""
    st.info(f"✏️ Editing: **{item['name']}** (ID: {item['item_id']})")

    # Find current category index
    current_cat = item.get("category_name", category_names[0])
    cat_idx = category_names.index(current_cat) if current_cat in category_names else 0

    with st.form("edit_item_form"):
        st.markdown("### ✏️ Edit Dish Details")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Dish Name *", value=item["name"])
            category_name = st.selectbox("Category *", category_names, index=cat_idx)
        with col2:
            price = st.number_input("Price (₹) *", min_value=1.0, value=float(item["price"]), step=10.0)
            image_url = st.text_input("Image URL", value=item.get("image_url", ""))

        description = st.text_area("Description", value=item.get("description", ""), height=80)

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancel Edit", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Dish name is required.")
            else:
                payload = {
                    "name": name.strip(),
                    "price": price,
                    "category_id": category_map.get(category_name, 1),
                    "description": description.strip(),
                    "image_url": image_url.strip()
                }
                res, err = api_put(f"/admin/menu/{item['item_id']}", payload)
                if err:
                    st.error(err)
                else:
                    st.success(f"✅ Updated **{name}** successfully!")
                    st.session_state.editing_item = None
                    st.rerun()

        if cancelled:
            st.session_state.editing_item = None
            st.rerun()
