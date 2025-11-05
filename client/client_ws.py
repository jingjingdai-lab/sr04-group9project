# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : client/client_ws.py
# Description :
#   Client graphique de détection YOLO (version WebSocket)
#   - Permet de choisir entre caméra ou fichier vidéo
#   - Détection YOLOv8 avec cadres et étiquettes
#   - Envoie le nombre de véhicules au serveur WebSocket
#   - Affiche en temps réel l’état du feu (rouge/jaune/vert)
#   - Redémarre automatiquement la vidéo et se reconnecte en cas de déconnexion
# =========================================================

import cv2
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from ultralytics import YOLO
from websocket import create_connection, WebSocketConnectionClosedException
import json
import os

# ---------- Configuration ----------
SERVER_URL = "ws://127.0.0.1:5001"
MODEL_NAME = "yolov8n.pt"
VEHICLE_CLASSES = {"car", "truck", "bus", "motorbike"}
WINDOW_TITLE = "SR04 - Détection de trafic (WebSocket)"
# -----------------------------------

print("Chargement du modèle YOLO...")
model = YOLO(MODEL_NAME)

# --- Variables globales ---
ws = None
detector_thread = None
video_path = None
led_color = "red"
running = True


# --- Connexion WebSocket ---
def ws_connect():
    """Établit une connexion WebSocket avec le serveur"""
    global ws
    while True:
        try:
            ws = create_connection(SERVER_URL)
            print("Connecté au serveur WebSocket.")
            return
        except Exception as e:
            print(f"Échec de la connexion WebSocket : {e}")
            print("Nouvelle tentative dans 3 secondes...")
            time.sleep(3)


# --- Thread de détection ---
def run_detection(source_type="camera", path=None):
    """Exécute la détection en temps réel sur la caméra ou une vidéo"""
    global led_color, running
    root.withdraw()  # Masquer la fenêtre principale Tkinter
    ws_connect()

    if source_type == "camera":
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        messagebox.showerror("Erreur", "Impossible d’ouvrir la source vidéo.")
        root.deiconify()
        return

    while running:
        ret, frame = cap.read()
        if not ret:
            # Redémarrage automatique de la vidéo
            if source_type == "video":
                try:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                except Exception:
                    print("Vidéo terminée, redémarrage du flux.")
                    cap.release()
                    cap = cv2.VideoCapture(path)
                    continue
            else:
                print("📷 Fin du flux caméra.")
                break

        # Détection avec YOLO
        results = model(frame, verbose=False)
        count = 0
        if results:
            r = results[0]
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                if label in VEHICLE_CLASSES:
                    count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Envoi du nombre de véhicules au serveur
        try:
            if ws:
                message = json.dumps({"vehicle_count": count})
                ws.send(message)
                # Réception de la réponse du serveur (état du feu)
                try:
                    response = ws.recv()
                    data = json.loads(response)
                    led_color = data.get("led", "red")
                except Exception:
                    pass
        except WebSocketConnectionClosedException:
            print("Connexion WebSocket perdue, reconnexion en cours...")
            ws_connect()

        # Dessin du feu tricolore à l’écran
        if led_color == "green":
            color = (0, 255, 0)
        elif led_color == "yellow":
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)

        cv2.circle(frame, (50, 50), 20, color, -1)
        cv2.putText(frame, f"Vehicles: {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow(WINDOW_TITLE, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Touche Échap → quitter
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify()
    if ws:
        ws.close()
    print("Détection terminée.")


# --- Fonctions GUI ---
def start_camera():
    """Lance la détection à partir de la caméra"""
    global detector_thread, running
    running = True
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "La détection est déjà en cours.")
        return
    detector_thread = threading.Thread(target=run_detection, args=("camera",), daemon=True)
    detector_thread.start()

def upload_video():
    """Lance la détection à partir d’un fichier vidéo choisi"""
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
    """Ferme proprement l’application"""
    global running
    running = False
    try:
        if ws:
            ws.close()
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()


# --- Interface graphique ---
root = tk.Tk()
root.title("SR04 Client de trafic intelligent (WebSocket)")
root.geometry("420x280")
root.resizable(False, False)

tk.Label(root, text="SR04 - Détection intelligente (WebSocket)",
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
