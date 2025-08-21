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

def run_reflex():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "-m", "reflex", "run", "app/reflex_app"], check=True)

def main():
    print("🚀 Starting AI-SDR Full Application...")
    print("📡 FastAPI Backend: http://localhost:8000")
    print("🌐 Reflex Frontend: http://localhost:3000")
    print("✨ Press Ctrl+C to stop both services")
    print("-" * 50)
    
    fastapi_process = Process(target=run_fastapi)
    fastapi_process.start()
    
    time.sleep(3)
    
    reflex_process = Process(target=run_reflex)
    reflex_process.start()
    
    def signal_handler(signum, frame):
        print("\n🛑 Stopping services...")
        fastapi_process.terminate()
        reflex_process.terminate()
        fastapi_process.join()
        reflex_process.join()
        print("✅ All services stopped.")
        sys.exit(0)
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while fastapi_process.is_alive() and reflex_process.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    if fastapi_process.is_alive():
        fastapi_process.terminate()
    if reflex_process.is_alive():
        reflex_process.terminate()

if __name__ == "__main__":
    main()
