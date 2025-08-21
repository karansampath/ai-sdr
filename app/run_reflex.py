"""Run script for the AI-SDR Reflex frontend."""

import subprocess
import sys
import os

def run_reflex():
    """Run the Reflex frontend application."""
    try:
        # Change to app directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run reflex
        subprocess.run([sys.executable, "-m", "reflex", "run", "reflex_app"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Reflex app: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nStopping Reflex app...")
        return 0

if __name__ == "__main__":
    sys.exit(run_reflex())
