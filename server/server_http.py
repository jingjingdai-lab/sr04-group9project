# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : server/server.py
# Description :
#   Contrôleur de feux de circulation basé sur Flask (HTTP)
#   - Moyenne mobile exponentielle (EMA) sur le nombre de véhicules
#   - Seuils d’hystérésis pour éviter le clignotement rapide
#   - Durées minimales et maximales pour chaque phase
#   - Phase jaune entre les états vert et rouge
# =========================================================

from flask import Flask, request, jsonify
from collections import deque
import time

app = Flask(__name__)

# --- Paramètres ajustables ---
LOW = 3              # Reste en ROUGE si la demande est inférieure à ce seuil (après la durée min rouge)
HIGH = 6             # Reste en VERT si la demande est supérieure à ce seuil (après la durée min verte)
ALPHA = 0.3          # Facteur de lissage EMA (0..1) ; plus grand = plus réactif
MIN_GREEN = 8        # Durée minimale en vert (secondes)
MAX_GREEN = 20       # Durée maximale en vert (secondes)
MIN_RED = 5          # Durée minimale en rouge (secondes)
YELLOW_TIME = 2      # Durée de la phase jaune (secondes)

# --- État du contrôleur ---
state = "RED"        # "RED" | "GREEN" | "YELLOW"
state_started_at = time.time()
ema = None           # Moyenne mobile exponentielle du nombre de véhicules
history = deque(maxlen=30)  # Historique optionnel pour un diagnostic futur

def now():
    """Renvoie le temps système actuel"""
    return time.time()

def elapsed():
    """Renvoie le temps écoulé depuis le dernier changement d’état"""
    return now() - state_started_at

def set_state(new_state):
    """Met à jour l’état du feu"""
    global state, state_started_at
    state = new_state
    state_started_at = now()

def update_logic(vehicle_count):
    """
    Met à jour l’état du contrôleur selon la demande lissée et les contraintes temporelles.
    Renvoie (couleur_du_feu, durée_suggérée_en_secondes)
    """
    global ema
    # 1) Appliquer le lissage EMA sur le nombre de véhicules détectés
    ema = vehicle_count if ema is None else (ALPHA * vehicle_count + (1 - ALPHA) * ema)
    history.append(ema)
    t = elapsed()

    # 2) Logique de transition entre les phases
    if state == "GREEN":
        # Respecter la durée minimale de la phase verte
        if t < MIN_GREEN:
            return "green", 1
        # Si la demande chute ou que la durée max est atteinte -> passer au jaune
        if ema < LOW or t >= MAX_GREEN:
            set_state("YELLOW")
            return "yellow", YELLOW_TIME
        # Sinon, rester en vert
        return "green", 1

    if state == "YELLOW":
        # Rester en jaune pour une durée fixe avant de passer au rouge
        if t >= YELLOW_TIME:
            set_state("RED")
            return "red", 1
        # Maintenir le jaune jusqu’à la fin du délai
        return "yellow", max(1, int(YELLOW_TIME - t))

    # État = ROUGE
    if t < MIN_RED:
        return "red", 1
    # Si la demande est suffisante, passer au vert
    if ema >= HIGH:
        set_state("GREEN")
        return "green", 1
    # Sinon, rester en rouge
    return "red", 1

@app.route("/traffic", methods=["POST"])
def traffic_control():
    """
    Corps de la requête : {"vehicle_count": <int>}
    Réponse : {"led": "red"|"yellow"|"green", "duration": <int secondes>, "ema": <float>}
    """
    data = request.get_json(force=True, silent=True) or {}
    vehicle_count = int(data.get("vehicle_count", 0))

    led, duration = update_logic(vehicle_count)
    print(f"count={vehicle_count:2d}  ema={ema:.2f}  state={state:<6}  -> led={led}, dur={duration}s")

    return jsonify({"led": led, "duration": int(duration), "ema": round(ema, 2)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
