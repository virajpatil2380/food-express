import streamlit as st
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.utils import init_cart_session
from frontend.views.auth import render_auth_view
from frontend.views.customer import render_customer_portal
from frontend.views.kitchen import render_kitchen_kds
from frontend.views.delivery import render_delivery_panel
from frontend.views.menu_mgr import render_menu_management
from frontend.views.analytics import render_analytics_dashboard

st.set_page_config(
    page_title="Food Express | Gourmet Delivery",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra Modern Animated UI & Food Card Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Smooth Fade In Up Animation */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 4px 15px rgba(255, 87, 34, 0.2); }
        50% { box-shadow: 0 8px 25px rgba(255, 87, 34, 0.4); }
        100% { box-shadow: 0 4px 15px rgba(255, 87, 34, 0.2); }
    }

    /* Card Wrapper Transitions & Hover Lift */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        border: 1px solid #FFE4D6 !important;
        border-radius: 18px !important;
        background: #FFFFFF !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
        transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        overflow: hidden;
    }

    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-6px) scale(1.01) !important;
        box-shadow: 0 14px 32px rgba(230, 81, 0, 0.16) !important;
        border-color: #FF7043 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        border-right: 2px solid #FFE0B2;
        background: linear-gradient(180deg, #FFFBF7 0%, #FFF3E0 100%);
    }

    /* Buttons Transitions & Pulsing Focus */
    .stFormSubmitButton>button,
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.55rem 1.3rem !important;
        box-shadow: 0 4px 14px rgba(255, 87, 34, 0.3) !important;
        transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }

    .stFormSubmitButton>button:hover,
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 8px 22px rgba(255, 87, 34, 0.45) !important;
        background: linear-gradient(135deg, #FF7043 0%, #D84315 100%) !important;
    }

    .stFormSubmitButton>button:active,
    .stButton>button[kind="primary"]:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* Regular Secondary Buttons */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: 1.5px solid #FFCCBC !important;
        background: #FFFFFF !important;
        transition: all 0.25s ease !important;
    }

    .stButton>button:hover {
        border-color: #FF5722 !important;
        color: #E64A19 !important;
        background-color: #FFF3E0 !important;
        transform: translateY(-2px);
    }

    /* Custom Input Fields */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 10px !important;
        border: 1px solid #FFE0B2 !important;
        transition: all 0.25s ease !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
        border-color: #FF5722 !important;
        box-shadow: 0 0 0 3px rgba(255, 87, 34, 0.15) !important;
    }

    /* Custom Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 15px !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 12px 22px !important;
        transition: all 0.25s ease !important;
    }

    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #FF5722 !important;
        color: #E64A19 !important;
        background: #FFF8F0 !important;
    }

    /* Image Rounding and Hover Zoom */
    [data-testid="stImage"] img {
        border-radius: 14px !important;
        transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1), filter 0.45s ease;
    }

    [data-testid="stImage"] img:hover {
        transform: scale(1.05);
    }

    /* Hide Streamlit default chrome */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def main():
    init_cart_session()

    if "user" not in st.session_state:
        st.session_state.user = None

    user = st.session_state.user

    # ─── NOT LOGGED IN ───
    if not user:
        render_auth_view()
        return

    # ─── LOGGED IN ───
    role = user.get("role", "Customer")

    # Sidebar Header
    st.sidebar.markdown("""
    <div style="text-align: left; padding: 10px 0 15px 0;">
        <span style="font-size: 38px;">🍔</span>
        <h2 style="display:inline; margin-left: 8px; color: #E65100; font-weight: 800; font-size: 24px;">Food Express</h2>
    </div>
    """, unsafe_allow_html=True)

    role_labels = {
        "Customer": "🛒 Gourmet Foodie",
        "Kitchen": "🍳 Kitchen Staff",
        "Delivery": "🚚 Delivery Partner",
        "Admin": "👑 Master Admin"
    }
    st.sidebar.info(f"👤 **{user['name']}**\n\nRole: `{role_labels.get(role, role)}`")

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        st.session_state.user = None
        st.session_state.cart = {}
        st.rerun()

    st.sidebar.divider()

    # ─── ROLE ROUTING ───
    if role == "Customer":
        cart_count = sum(i["qty"] for i in st.session_state.cart.values())
        if cart_count > 0:
            st.sidebar.success(f"🛒 **{cart_count} item(s)** in your cart")
        render_customer_portal()

    elif role == "Kitchen":
        render_kitchen_kds()

    elif role == "Delivery":
        render_delivery_panel()

    elif role == "Admin":
        page = st.sidebar.radio(
            "Admin Navigation",
            ["📊 Analytics Dashboard", "📦 Menu & Inventory", "🍳 Kitchen Display", "🚚 Delivery Tracking"],
            label_visibility="collapsed"
        )
        if page == "📊 Analytics Dashboard":
            render_analytics_dashboard()
        elif page == "📦 Menu & Inventory":
            render_menu_management()
        elif page == "🍳 Kitchen Display":
            render_kitchen_kds()
        elif page == "🚚 Delivery Tracking":
            render_delivery_panel()

    else:
        st.error("⛔ Access denied.")
        if st.button("Sign Out"):
            st.session_state.user = None
            st.rerun()


if __name__ == "__main__":
    main()
