# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : server/server_mqtt.py
# Description :
#   Contrôleur de feux de circulation basé sur MQTT
#   - S’abonne au topic "traffic/vehicle_count"
#   - Publie sur le topic "traffic/led" la couleur du feu
# =========================================================

import time
import json
import paho.mqtt.client as mqtt

# --- Paramètres du serveur MQTT ---
BROKER = "localhost"
PORT = 1883
TOPIC_COUNT = "traffic/vehicle_count"
TOPIC_LED = "traffic/led"

# --- Paramètres logiques du feu de circulation ---
LOW = 3
HIGH = 6
ALPHA = 0.3
MIN_GREEN = 8
MAX_GREEN = 20
MIN_RED = 5
YELLOW_TIME = 2

# --- État du contrôleur ---
state = "RED"
state_started_at = time.time()
ema = None

def elapsed():
    """Renvoie le temps écoulé depuis le dernier changement d’état"""
    return time.time() - state_started_at

def set_state(new_state):
    """Met à jour l’état actuel du feu"""
    global state, state_started_at
    state = new_state
    state_started_at = time.time()

def update_logic(vehicle_count):
    """Calcule la logique du feu à partir du nombre de véhicules détectés"""
    global ema, state
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

    if t < MIN_RED:
        return "red"
    if ema >= HIGH:
        set_state("GREEN")
        return "green"
    return "red"

# --- Fonctions de rappel MQTT ---
def on_connect(client, userdata, flags, rc):
    """Appelée lors de la connexion au broker"""
    print(f"Connecté au broker MQTT ({BROKER}:{PORT}) avec le code {rc}")
    client.subscribe(TOPIC_COUNT)

def on_message(client, userdata, msg):
    """Appelée lorsqu’un message est reçu sur le topic 'traffic/vehicle_count'"""
    try:
        payload = json.loads(msg.payload.decode())
        vehicle_count = int(payload.get("vehicle_count", 0))
        led = update_logic(vehicle_count)
        response = {"led": led}
        client.publish(TOPIC_LED, json.dumps(response))
        print(f"count={vehicle_count:2d}  ema={ema:.2f}  state={state:<6} -> led={led}")
    except Exception as e:
        print("Erreur lors du traitement du message :", e)

# --- Point d’entrée principal ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Serveur de trafic MQTT en cours de démarrage...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
