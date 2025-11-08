# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : client/client_mqtt.py
# Description :
#   Client graphique de détection YOLO utilisant le protocole MQTT
#   - Utilise le module VehicleDetector (YOLOv8)
#   - Publie le nombre de véhicules sur "traffic/vehicle_count"
#   - S’abonne au topic "traffic/led" pour recevoir la couleur du feu
#   - Mesure la latence + taille du message, et les enregistre dans un fichier CSV
# =========================================================

import cv2
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import csv
import os
import sys
import paho.mqtt.client as mqtt
from detector import VehicleDetector  # 🔹 Import du module YOLO commun

# --- Paramètres MQTT et configuration YOLO ---
BROKER = "localhost"
PORT = 1883
TOPIC_COUNT = "traffic/vehicle_count"
TOPIC_LED = "traffic/led"
MODEL_NAME = "yolov8n.pt"
LAT_FILE = "latency_mqtt.csv"
WINDOW_TITLE = "SR04 - Détection de trafic (MQTT)"
RESET_LATENCY_FILE = True  # 🧹 True = recrée le CSV à chaque exécution
# ---------------------------------------------

# --- Initialisation du détecteur ---
detector = VehicleDetector(model_name=MODEL_NAME, latency_file=LAT_FILE)

# --- Initialisation du fichier CSV ---
if RESET_LATENCY_FILE or not os.path.exists(LAT_FILE):
    with open(LAT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "latency_ms", "msg_size_bytes"])

# --- Variables globales ---
client = None
led_color = "red"
detector_thread = None
video_path = None
running = True


# --- Fonctions de rappel MQTT ---
def on_connect(client, userdata, flags, rc):
    """Appelée lors de la connexion au broker MQTT."""
    print(f"Connecté au broker MQTT ({BROKER}:{PORT})")
    client.subscribe(TOPIC_LED)


def on_message(client, userdata, msg):
    """Appelée lorsqu’un message est reçu sur le topic 'traffic/led'."""
    global led_color
    try:
        data = json.loads(msg.payload.decode())
        led_color = data.get("led", "red")
    except Exception:
        pass


# --- Connexion au broker MQTT ---
def mqtt_connect():
    """Établit la connexion avec le broker MQTT et démarre l’écoute en arrière-plan."""
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()


# --- Détection principale ---
def run_detection(source_type="camera", path=None):
    """Effectue la détection en temps réel et communique via MQTT."""
    global running
    root.withdraw()
    mqtt_connect()

    cap = cv2.VideoCapture(0 if source_type == "camera" else path)
    if not cap.isOpened():
        messagebox.showerror("Erreur", "Impossible d’ouvrir la source vidéo.")
        root.deiconify()
        return

    last_latency = 0
    last_msg_size = 0

    while running:
        ret, frame = cap.read()
        if not ret:
            if source_type == "video":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                break

        # --- Détection via le module YOLO ---
        count, frame = detector.detect(frame)

        # --- Publication MQTT + mesure latence + taille message ---
        try:
            payload = json.dumps({"vehicle_count": count})
            msg_size = sys.getsizeof(payload)

            t_start = time.time()
            client.publish(TOPIC_COUNT, payload)
            t_end = time.time()
            latency = (t_end - t_start) * 1000  # en ms
            last_latency = latency
            last_msg_size = msg_size

            # Enregistre dans le CSV
            with open(LAT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([time.time(), round(latency, 2), msg_size])

        except Exception as e:
            print(f"Erreur de publication MQTT : {e}")

        # --- Dessin du feu tricolore ---
        detector.draw_traffic_light(frame, led_color)

        # --- Affichage des informations ---
        cv2.putText(frame, f"Vehicules : {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Latence : {last_latency:.1f} ms", (10, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        cv2.putText(frame, f"Taille msg : {last_msg_size} o", (10, 155),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)

        cv2.imshow(WINDOW_TITLE, frame)

        if cv2.waitKey(1) & 0xFF == 27:
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify()


# --- Interface graphique (GUI) ---
def start_camera():
    """Lance la détection depuis la caméra."""
    global detector_thread, running
    running = True
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "La détection est déjà en cours.")
        return
    detector_thread = threading.Thread(target=run_detection, args=("camera",), daemon=True)
    detector_thread.start()


def upload_video():
    """Lance la détection depuis un fichier vidéo."""
    global detector_thread, running, video_path
    running = True
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "La détection est déjà en cours.")
        return
    path = filedialog.askopenfilename(
        title="Choisir une vidéo",
        filetypes=[("Fichiers vidéo", "*.mp4 *.avi *.mov *.mkv"), ("Tous les fichiers", "*.*")]
    )
    if not path:
        return
    video_path = path
    detector_thread = threading.Thread(target=run_detection, args=("video", path), daemon=True)
    detector_thread.start()


def exit_app():
    """Ferme proprement l’application."""
    global running
    running = False
    try:
        if client:
            client.disconnect()
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()


# --- Fenêtre principale ---
root = tk.Tk()
root.title("SR04 - Client de trafic intelligent (MQTT)")
root.geometry("420x280")
root.resizable(False, False)

tk.Label(root, text="SR04 Groupe 9 - Détection intelligente (MQTT)",
         font=("Segoe UI", 14, "bold")).pack(pady=15)

tk.Button(root, text="Ouvrir la caméra",
          command=start_camera, width=22, height=2,
          bg="#4CAF50", fg="white").pack(pady=6)

tk.Button(root, text="Choisir une vidéo",
          command=upload_video, width=22, height=2,
          bg="#2196F3", fg="white").pack(pady=6)

tk.Button(root, text="Quitter",
          command=exit_app, width=22, height=2,
          bg="#f44336", fg="white").pack(pady=12)

root.mainloop()
