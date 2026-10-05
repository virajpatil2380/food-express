import requests
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

API_BASE = Config.API_BASE_URL

def _format_error(response):
    try:
        data = response.json()
        if isinstance(data, dict) and "error" in data:
            return data["error"]
    except Exception:
        pass
    return f"API Error ({response.status_code}): {response.text}"

def api_get(endpoint, params=None):
    try:
        response = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return None, _format_error(response)
    except requests.exceptions.ConnectionError:
        return None, f"Unable to connect to Flask API server at {API_BASE}. Please make sure the Flask backend is running."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def api_post(endpoint, json_data):
    try:
        response = requests.post(f"{API_BASE}{endpoint}", json=json_data, timeout=5)
        if response.status_code in [200, 201]:
            return response.json(), None
        return None, _format_error(response)
    except requests.exceptions.ConnectionError:
        return None, f"Unable to connect to Flask API server at {API_BASE}. Please verify backend status."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def api_put(endpoint, json_data):
    try:
        response = requests.put(f"{API_BASE}{endpoint}", json=json_data, timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return None, _format_error(response)
    except requests.exceptions.ConnectionError:
        return None, f"Unable to connect to Flask API server at {API_BASE}."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def api_delete(endpoint):
    try:
        response = requests.delete(f"{API_BASE}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return None, _format_error(response)
    except requests.exceptions.ConnectionError:
        return None, f"Unable to connect to Flask API server at {API_BASE}."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def init_cart_session():
    """Initializes persistent cart state in Streamlit session_state."""
    if "cart" not in st.session_state:
        st.session_state.cart = {}  # {item_id: {name, price, qty, description, category_name}}
    if "tracked_order_id" not in st.session_state:
        st.session_state.tracked_order_id = None
