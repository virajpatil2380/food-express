import subprocess
import sys
import time
import os

os.environ["PYTHONIOENCODING"] = "utf-8"


def main():
    print("=" * 60)
    print("STARTING FOOD EXPRESS FULL-STACK APPLICATION")
    print("=" * 60)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    flask_script = os.path.join(project_dir, "backend", "app.py")
    streamlit_script = os.path.join(project_dir, "frontend", "app.py")

    print("\n[1/2] Launching Flask API (http://127.0.0.1:5000)...")
    flask_process = subprocess.Popen(
        [sys.executable, flask_script],
        cwd=project_dir
    )

    time.sleep(2)

    print("[2/2] Launching Streamlit UI (http://localhost:8501)...")
    try:
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", streamlit_script],
            cwd=project_dir
        )
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        flask_process.terminate()
        print("Application stopped.")


if __name__ == "__main__":
    main()
