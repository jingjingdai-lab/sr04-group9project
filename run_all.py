# =========================================================
# SR04 Group 9 Project
# File: run_all.py
# Description:
#   Launch Flask server + YOLO client GUI automatically.
#   One-click startup for the SR04 Smart Traffic System.
# =========================================================

import subprocess
import time
import sys
import requests
import os
import signal

# Paths
SERVER_PATH = os.path.join("server", "server.py")
CLIENT_PATH = os.path.join("client", "client.py")

# Ensure both files exist
if not os.path.exists(SERVER_PATH):
    print("server/server.py not found.")
    sys.exit(1)
if not os.path.exists(CLIENT_PATH):
    print("client/client.py not found.")
    sys.exit(1)

# ---------------------------------------------------------
# Start Flask server
# ---------------------------------------------------------
print("Starting Flask server...")
server_proc = subprocess.Popen([sys.executable, SERVER_PATH])

# Wait until server responds
url = "http://127.0.0.1:5000/traffic"
for i in range(15):
    try:
        requests.post(url, json={"vehicle_count": 0}, timeout=1.0)
        print("Flask server is up.")
        break
    except Exception:
        print(f"Waiting for server... ({i+1}/15)")
        time.sleep(1)
else:
    print("Server failed to start. Check for errors in server window.")
    server_proc.terminate()
    sys.exit(1)

# ---------------------------------------------------------
# Start client GUI
# ---------------------------------------------------------
print("Launching YOLO client GUI...")
try:
    client_proc = subprocess.Popen([sys.executable, CLIENT_PATH])
except KeyboardInterrupt:
    print("\nInterrupted before starting client.")
    server_proc.terminate()
    sys.exit(0)


# Wait until client exits
try:
    client_proc.wait()
except KeyboardInterrupt:
    print("\nCtrl+C pressed — stopping all processes.")
finally:
    print("Stopping server...")
    if os.name == "nt":
        server_proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        server_proc.terminate()
    server_proc.wait()
    print("Server stopped. All done.")

