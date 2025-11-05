# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : server/server_ws.py
# Description :
#   Contrôleur de feux de circulation asynchrone basé sur WebSocket
#   - Reçoit le nombre de véhicules depuis les clients
#   - Calcule la couleur du feu (rouge/jaune/vert) en temps réel
#   - Envoie l’état du feu à chaque client connecté
# =========================================================

import asyncio
import websockets
import json
import time

# --- Paramètres du serveur ---
HOST = "127.0.0.1"
PORT = 5001

# --- Paramètres logiques du feu de circulation ---
LOW = 3
HIGH = 6
ALPHA = 0.3
MIN_GREEN = 8
MAX_GREEN = 20
MIN_RED = 5
YELLOW_TIME = 2

# --- État du contrôleur ---
state = "RED"        # "RED" | "YELLOW" | "GREEN"
state_started_at = time.time()
ema = None           # moyenne mobile exponentielle du nombre de véhicules

# --- Fonctions utilitaires ---
def elapsed():
    """Renvoie le temps écoulé depuis le dernier changement d’état"""
    return time.time() - state_started_at

def set_state(new_state):
    """Change l’état du feu de circulation"""
    global state, state_started_at
    state = new_state
    state_started_at = time.time()

def update_logic(vehicle_count: int) -> str:
    """Met à jour la logique du feu et renvoie la couleur actuelle"""
    global ema
    global state

    ema = vehicle_count if ema is None else (ALPHA * vehicle_count + (1 - ALPHA) * ema)
    t = elapsed()

    if state == "GREEN":
        if t < MIN_GREEN:
            return "green"
        if ema < LOW or t >= MAX_GREEN:
            set_state("YELLOW")
            return "yellow"
        return "green"

    if state == "YELLOW":
        if t >= YELLOW_TIME:
            set_state("RED")
            return "red"
        return "yellow"

    # état == "RED"
    if t < MIN_RED:
        return "red"
    if ema >= HIGH:
        set_state("GREEN")
        return "green"
    return "red"


# --- Gestion des connexions WebSocket ---
async def handle_client(websocket):
    """Gère la connexion d’un client"""
    print("🔗 Client connecté.")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                vehicle_count = int(data.get("vehicle_count", 0))
                led = update_logic(vehicle_count)
                response = {"led": led}
                await websocket.send(json.dumps(response))
                print(f"count={vehicle_count:2d}  ema={ema:.2f}  state={state:<6}  -> led={led}")
            except json.JSONDecodeError:
                print("⚠️ Message reçu invalide :", message)
    except websockets.exceptions.ConnectionClosed:
        print("Client déconnecté.")


# --- Point d’entrée principal ---
async def main():
    print(f"🚦 Serveur WebSocket en cours d’exécution sur ws://{HOST}:{PORT}")
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # exécution continue

if __name__ == "__main__":
    asyncio.run(main())

