# =========================================================
# SR04 Group 9 Project
# File: server/server.py
# Description:
#   Smoothed, hysteresis-based traffic signal controller.
#   - Exponential Moving Average (EMA) on vehicle counts
#   - Hysteresis thresholds to avoid flicker
#   - Min/Max phase durations
#   - Yellow phase between green and red
# =========================================================

from flask import Flask, request, jsonify
from collections import deque
import time

app = Flask(__name__)

# --- Tunable parameters ---
LOW = 3              # go/stay RED if demand is below this (after min red)
HIGH = 6             # go/stay GREEN if demand is above this (after min green)
ALPHA = 0.3          # EMA smoothing factor (0..1), higher = more reactive
MIN_GREEN = 8        # seconds
MAX_GREEN = 20       # seconds
MIN_RED = 5          # seconds
YELLOW_TIME = 2      # seconds

# --- Controller state ---
state = "RED"        # "RED" | "GREEN" | "YELLOW"
state_started_at = time.time()
ema = None           # exponential moving average of vehicle_count
history = deque(maxlen=30)  # optional, for future diagnostics

def now():
    return time.time()

def elapsed():
    return now() - state_started_at

def set_state(new_state):
    global state, state_started_at
    state = new_state
    state_started_at = now()

def update_logic(vehicle_count):
    """
    Update controller state based on smoothed demand and timing constraints.
    Returns (led_color, suggested_duration_seconds)
    """
    global ema
    # 1) Smooth the input
    ema = vehicle_count if ema is None else (ALPHA * vehicle_count + (1 - ALPHA) * ema)
    history.append(ema)
    t = elapsed()

    # 2) Phase logic with timing
    if state == "GREEN":
        # Always respect minimum green time
        if t < MIN_GREEN:
            return "green", 1
        # If demand dropped significantly or max green reached -> go YELLOW
        if ema < LOW or t >= MAX_GREEN:
            set_state("YELLOW")
            return "yellow", YELLOW_TIME
        # otherwise stay GREEN
        return "green", 1

    if state == "YELLOW":
        # Stay yellow for fixed time, then go RED
        if t >= YELLOW_TIME:
            set_state("RED")
            return "red", 1
        # keep yellow until timeout
        return "yellow", max(1, int(YELLOW_TIME - t))

    # state == "RED"
    if t < MIN_RED:
        return "red", 1
    # Enough demand? transition to GREEN
    if ema >= HIGH:
        set_state("GREEN")
        return "green", 1
    # otherwise stay RED
    return "red", 1

@app.route("/traffic", methods=["POST"])
def traffic_control():
    """
    Request body: {"vehicle_count": <int>}
    Response: {"led": "red"|"yellow"|"green", "duration": <int seconds>, "ema": <float>}
    """
    data = request.get_json(force=True, silent=True) or {}
    vehicle_count = int(data.get("vehicle_count", 0))

    led, duration = update_logic(vehicle_count)
    print(f"count={vehicle_count:2d}  ema={ema:.2f}  state={state:<6}  -> led={led}, dur={duration}s")

    return jsonify({"led": led, "duration": int(duration), "ema": round(ema, 2)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
