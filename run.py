#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
import os
from multiprocessing import Process

def run_fastapi():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "src/main.py"], check=True)

def run_streamlit():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/frontend")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8501"], check=True)

def main():
    print("🚀 Starting AI-SDR Full Application...")
    print("📡 FastAPI Backend: http://localhost:8000")
    print("🌐 Streamlit Frontend: http://localhost:8501")
    print("✨ Press Ctrl+C to stop both services")
    print("-" * 50)
    
    fastapi_process = Process(target=run_fastapi)
    fastapi_process.start()
    
    time.sleep(3)
    
    streamlit_process = Process(target=run_streamlit)
    streamlit_process.start()
    
    def signal_handler(signum, frame):
        print("\n🛑 Stopping services...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        fastapi_process.join()
        streamlit_process.join()
        print("✅ All services stopped.")
        sys.exit(0)
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while fastapi_process.is_alive() and streamlit_process.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    if fastapi_process.is_alive():
        fastapi_process.terminate()
    if streamlit_process.is_alive():
        streamlit_process.terminate()

if __name__ == "__main__":
    main()
