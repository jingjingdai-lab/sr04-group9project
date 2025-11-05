# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : client/client_mqtt.py
# Description :
#   Client de détection YOLO utilisant le protocole MQTT
#   - Publie le nombre de véhicules sur "traffic/vehicle_count"
#   - S’abonne au topic "traffic/led" pour recevoir la couleur du feu
# =========================================================

import cv2
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import json
import os

# --- Paramètres MQTT et modèle YOLO ---
BROKER = "localhost"
PORT = 1883
TOPIC_COUNT = "traffic/vehicle_count"
TOPIC_LED = "traffic/led"
MODEL_NAME = "yolov8n.pt"
VEHICLE_CLASSES = {"car", "truck", "bus", "motorbike"}
WINDOW_TITLE = "SR04 - Détection de trafic (MQTT)"

print("Chargement du modèle YOLO...")
model = YOLO(MODEL_NAME)

# --- Variables globales ---
client = None
led_color = "red"
detector_thread = None
video_path = None
running = True

# --- Fonctions de rappel MQTT ---
def on_connect(client, userdata, flags, rc):
    """Appelée lors de la connexion au broker MQTT"""
    print(f"✅ Connecté au broker MQTT ({BROKER}:{PORT})")
    client.subscribe(TOPIC_LED)

def on_message(client, userdata, msg):
    """Appelée lorsqu’un message est reçu sur le topic 'traffic/led'"""
    global led_color
    try:
        data = json.loads(msg.payload.decode())
        led_color = data.get("led", "red")
    except Exception:
        pass

# --- Connexion au broker MQTT ---
def mqtt_connect():
    """Établit la connexion avec le broker MQTT et démarre l’écoute en arrière-plan"""
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()

# --- Détection principale ---
def run_detection(source_type="camera", path=None):
    """Effectue la détection en temps réel et communique via MQTT"""
    global running
    root.withdraw()
    mqtt_connect()

    cap = cv2.VideoCapture(0 if source_type == "camera" else path)
    if not cap.isOpened():
        messagebox.showerror("Erreur", "Impossible d’ouvrir la source vidéo.")
        root.deiconify()
        return

    while running:
        ret, frame = cap.read()
        if not ret:
            # Redémarre automatiquement la vidéo si nécessaire
            if source_type == "video":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                break

        # Détection avec YOLO
        results = model(frame, verbose=False)
        count = 0
        if results:
            for box in results[0].boxes:
                label = model.names[int(box.cls[0])]
                if label in VEHICLE_CLASSES:
                    count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Publication du nombre de véhicules détectés
        client.publish(TOPIC_COUNT, json.dumps({"vehicle_count": count}))

        # Dessin du feu tricolore selon la couleur reçue
        color = (0, 0, 255) if led_color == "red" else (0, 255, 255) if led_color == "yellow" else (0, 255, 0)
        cv2.circle(frame, (50, 50), 20, color, -1)
        cv2.putText(frame, f"Vehicles: {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow(WINDOW_TITLE, frame)

        # Quitter avec la touche Échap
        if cv2.waitKey(1) & 0xFF == 27:
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify()

# --- Interface graphique (GUI) ---
def start_camera():
    """Lance la détection depuis la caméra"""
    global detector_thread, running
    running = True
    if detector_thread and detector_thread.is_alive():
        return
    detector_thread = threading.Thread(target=run_detection, args=("camera",), daemon=True)
    detector_thread.start()

def upload_video():
    """Lance la détection depuis un fichier vidéo"""
    global detector_thread, running, video_path
    running = True
    if detector_thread and detector_thread.is_alive():
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
    """Ferme proprement l’application"""
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

tk.Label(root, text="SR04 - Détection intelligente (MQTT)",
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

