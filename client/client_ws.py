# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : client/client_ws.py
# Description :
#   Client graphique de détection YOLO (version WebSocket)
#   - Utilise le module VehicleDetector (YOLOv8)
#   - Permet de choisir entre caméra ou fichier vidéo
#   - Envoie le nombre de véhicules au serveur WebSocket
#   - Mesure la latence + taille du message, et les sauvegarde dans un fichier CSV
#   - Affiche en temps réel l’état du feu (rouge/jaune/vert)
#   - Redémarre automatiquement la vidéo et se reconnecte en cas de déconnexion
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
from websocket import create_connection, WebSocketConnectionClosedException
from detector import VehicleDetector  # 🔹 Module commun pour la détection YOLO

# ---------- Configuration ----------
SERVER_URL = "ws://127.0.0.1:5001"
MODEL_NAME = "yolov8n.pt"
LAT_FILE = "latency_ws.csv"
WINDOW_TITLE = "SR04 - Détection de trafic (WebSocket)"
RESET_LATENCY_FILE = True  # 🧹 True = recrée le fichier CSV à chaque exécution
# -----------------------------------

# --- Initialisation du détecteur YOLO ---
detector = VehicleDetector(model_name=MODEL_NAME, latency_file=LAT_FILE)

# --- Préparation du fichier CSV ---
if RESET_LATENCY_FILE or not os.path.exists(LAT_FILE):
    with open(LAT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "latency_ms", "msg_size_bytes"])

# --- Variables globales ---
ws = None
detector_thread = None
video_path = None
led_color = "red"
running = True


# --- Connexion WebSocket ---
def ws_connect():
    """Établit une connexion WebSocket avec le serveur (avec tentatives automatiques)."""
    global ws
    while True:
        try:
            ws = create_connection(SERVER_URL)
            print(f"Connecté au serveur WebSocket ({SERVER_URL})")
            return
        except Exception as e:
            print(f"Échec de la connexion WebSocket : {e}")
            print("⏳ Nouvelle tentative dans 3 secondes...")
            time.sleep(3)


# --- Thread principal de détection ---
def run_detection(source_type="camera", path=None):
    """Exécute la détection en temps réel (caméra ou vidéo) et communique via WebSocket."""
    global led_color, running
    root.withdraw()  # Masquer la fenêtre principale
    ws_connect()

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
                try:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                except Exception:
                    cap.release()
                    cap = cv2.VideoCapture(path)
                    continue
            else:
                print("📷 Fin du flux caméra.")
                break

        # --- Détection YOLO via le module ---
        count, frame = detector.detect(frame)

        # --- Envoi des données + mesure de latence + taille du message ---
        try:
            if ws:
                message = json.dumps({"vehicle_count": count})
                msg_size = sys.getsizeof(message)

                t_start = time.time()
                ws.send(message)
                response = ws.recv()
                t_end = time.time()
                latency = (t_end - t_start) * 1000  # en millisecondes
                last_latency = latency
                last_msg_size = msg_size

                # Enregistre la latence et la taille du message dans le fichier CSV
                with open(LAT_FILE, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([time.time(), round(latency, 2), msg_size])

                # Mise à jour de l’état du feu
                data = json.loads(response)
                led_color = data.get("led", "red")

        except WebSocketConnectionClosedException:
            print("Connexion WebSocket perdue, reconnexion...")
            ws_connect()
        except Exception as e:
            print(f"Erreur de communication WebSocket : {e}")

        # --- Affichage du feu tricolore ---
        detector.draw_traffic_light(frame, led_color)

        # --- Informations à l’écran ---
        cv2.putText(frame, f"Vehicules : {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Latence : {last_latency:.1f} ms", (10, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        cv2.putText(frame, f"Taille msg : {last_msg_size} o", (10, 155),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)

        # --- Fenêtre OpenCV ---
        cv2.imshow(WINDOW_TITLE, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify()
    if ws:
        ws.close()
    print("🛑 Détection terminée.")


# --- Interface graphique ---
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
        if ws:
            ws.close()
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()


# --- Fenêtre principale Tkinter ---
root = tk.Tk()
root.title("SR04 - Client de trafic intelligent (WebSocket)")
root.geometry("420x280")
root.resizable(False, False)

tk.Label(root, text="SR04 Groupe 9 - Détection intelligente (WebSocket)",
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
