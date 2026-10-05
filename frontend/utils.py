import requests
import streamlit as st
import os
import sys
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

# Check Streamlit secrets or environment variable or Config
API_BASE = os.getenv("API_BASE_URL") or getattr(st, "secrets", {}).get("API_BASE_URL", Config.API_BASE_URL)

# Auto-start Flask in background thread if running on cloud / single container without separate Flask process
_FLASK_STARTED = False

def _ensure_flask_running():
    global _FLASK_STARTED
    if _FLASK_STARTED:
        return
    
    # Ping backend to check if already running
    try:
        r = requests.get(f"{API_BASE.replace('/api', '')}/", timeout=1)
        if r.status_code == 200:
            _FLASK_STARTED = True
            return
    except Exception:
        pass

    # If backend is not responding (e.g. Streamlit Cloud single container), launch Flask in background thread
    def run_flask_in_thread():
        try:
            from backend.app import app
            app.run(host="127.0.0.1", port=Config.FLASK_PORT, debug=False, use_reloader=False)
        except Exception as e:
            print("Background Flask start notice:", e)

    t = threading.Thread(target=run_flask_in_thread, daemon=True)
    t.start()
    _FLASK_STARTED = True
    time.sleep(1.5)

# Ensure Flask is running on app load
_ensure_flask_running()


def _format_error(response):
    try:
        data = response.json()
        if isinstance(data, dict) and "error" in data:
            return data["error"]
    except Exception:
        pass
    return f"API Error ({response.status_code}): {response.text}"


def api_get(endpoint, params=None):
    _ensure_flask_running()
    try:
        response = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return None, _format_error(response)
    except requests.exceptions.ConnectionError:
        return None, f"Unable to connect to Flask API server at {API_BASE}. Please make sure backend is active."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def api_post(endpoint, json_data):
    _ensure_flask_running()
    try:
        response = requests.post(f"{API_BASE}{endpoint}", json=json_data, timeout=5)
        if response.status_code in [200, 201]:
            return response.json(), None
        return None, _format_error(response)
    except requests.exceptions.ConnectionError:
        return None, f"Unable to connect to Flask API server at {API_BASE}."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def api_put(endpoint, json_data):
    _ensure_flask_running()
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
    _ensure_flask_running()
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
        st.session_state.cart = {}
    if "tracked_order_id" not in st.session_state:
        st.session_state.tracked_order_id = None
