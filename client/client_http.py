# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : client/client_http.py
# Description :
#   Client graphique de détection YOLO (version HTTP)
#   - Interface Tkinter : Ouvrir la caméra / Charger une vidéo
#   - Utilise le module VehicleDetector (YOLOv8)
#   - Envoie le nombre de véhicules au serveur Flask
#   - Mesure la latence et l’enregistre dans un fichier CSV
#   - Affiche un feu tricolore virtuel (rouge / jaune / vert)
# =========================================================

import cv2
import requests
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import csv
import os
from detector import VehicleDetector  # 🔹 module externe pour la détection YOLO

# ---------- Configuration ----------
SERVER_URL = "http://127.0.0.1:5000/traffic"
MODEL_NAME = "yolov8n.pt"
LAT_FILE = "latency_http.csv"
WINDOW_TITLE = "SR04 - Détection de trafic (HTTP)"
# -----------------------------------

# --- Initialisation du détecteur YOLO ---
detector = VehicleDetector(model_name=MODEL_NAME, latency_file=LAT_FILE)

# --- Création du fichier CSV s’il n’existe pas ---
if not os.path.exists(LAT_FILE):
    with open(LAT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "latency_ms"])

# --- Fenêtre principale Tkinter ---
root = tk.Tk()
root.title("SR04 - Client de trafic intelligent (HTTP)")
root.geometry("420x280")
root.resizable(False, False)

# --- Gestion du thread de détection ---
detector_thread = None


def run_detection(source_type: str, path: str | None = None):
    """
    Exécute la boucle principale de détection dans un thread séparé.
    :param source_type: "camera" ou "video"
    :param path: chemin du fichier vidéo si source_type == "video"
    """
    root.withdraw()  # Masquer la fenêtre principale pendant la détection

    # --- Ouverture de la source vidéo ---
    if source_type == "camera":
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d’ouvrir la caméra.")
            root.deiconify()
            return
    else:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d’ouvrir la vidéo sélectionnée.")
            root.deiconify()
            return

    while True:
        ret, frame = cap.read()
        if not ret:
            # Redémarre la vidéo automatiquement
            if source_type == "video":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                break

        # --- Détection via le module VehicleDetector ---
        count, frame = detector.detect(frame)

        # --- Mesure et enregistrement de la latence HTTP ---
        try:
            t_start = time.time()
            res = requests.post(SERVER_URL, json={"vehicle_count": count}, timeout=1.0)
            t_end = time.time()
            latency = (t_end - t_start) * 1000  # millisecondes

            # Enregistre la latence dans le fichier CSV
            with open(LAT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([time.time(), latency])

            led = res.json().get("led", "red")
        except Exception:
            led = "red"

        # --- Dessin du feu tricolore ---
        detector.draw_traffic_light(frame, led)

        # --- Affichage du nombre de véhicules + latence ---
        cv2.putText(frame, f"Vehicules : {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Latence : {latency:.1f} ms", (10, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        # --- Affiche la fenêtre OpenCV ---
        cv2.imshow(WINDOW_TITLE, frame)

        # Quitter avec la touche Échap
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify()  # Réaffiche la fenêtre principale


def start_camera():
    """Lance la détection à partir de la caméra."""
    global detector_thread
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "La détection est déjà en cours.")
        return
    detector_thread = threading.Thread(target=run_detection, args=("camera",), daemon=True)
    detector_thread.start()


def upload_video():
    """Lance la détection à partir d’un fichier vidéo."""
    global detector_thread
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "La détection est déjà en cours.")
        return
    path = filedialog.askopenfilename(
        title="Sélectionner un fichier vidéo",
        filetypes=[("Fichiers vidéo", "*.mp4 *.avi *.mov *.mkv"), ("Tous les fichiers", "*.*")]
    )
    if not path:
        return
    detector_thread = threading.Thread(target=run_detection, args=("video", path), daemon=True)
    detector_thread.start()


def exit_app():
    """Ferme proprement l’application."""
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()


# --- Interface graphique ---
tk.Label(root, text="SR04 Groupe 9 - Détection intelligente (HTTP)",
         font=("Segoe UI", 14, "bold")).pack(pady=18)

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
