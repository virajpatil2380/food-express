import streamlit as st
from frontend.utils import api_post


def render_auth_view():
    """Clean login/signup page — customers only signup, staff uses pre-assigned credentials."""

    _, center, _ = st.columns([1.2, 2, 1.2])

    with center:
        st.markdown("# 🍔 Food Express")
        st.caption("Fresh • Fast • Delicious")

        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if login_btn:
                    if not email or not password:
                        st.error("Enter email and password.")
                    else:
                        res, err = api_post("/auth/login", {
                            "email": email.strip(),
                            "password": password.strip()
                        })
                        if err:
                            st.error(err)
                        else:
                            st.session_state.user = res["user"]
                            st.rerun()

        with tab_signup:
            st.caption("New here? Create a customer account.")
            with st.form("signup_form"):
                name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="john@example.com")
                phone = st.text_input("Phone", placeholder="9876543210")
                password = st.text_input("Password", type="password")

                signup_btn = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                if signup_btn:
                    if not all([name, email, phone, password]):
                        st.error("All fields are required.")
                    else:
                        res, err = api_post("/auth/signup", {
                            "name": name.strip(),
                            "email": email.strip(),
                            "phone": phone.strip(),
                            "password": password.strip(),
                            "role": "Customer"
                        })
                        if err:
                            st.error(err)
                        else:
                            st.success("Account created! Sign in now.")
