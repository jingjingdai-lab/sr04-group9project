# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : client/client.py
# Description :
#   Client graphique de détection YOLO (version HTTP)
#   - Interface Tkinter : Ouvrir la caméra / Charger une vidéo
#   - Détection YOLOv8 avec cadres et étiquettes
#   - Envoie le nombre de véhicules au serveur Flask
#   - Affiche un feu tricolore virtuel (rouge/jaune/vert)
# =========================================================

import cv2
import requests
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from ultralytics import YOLO

# ---------- Configuration ----------
SERVER_URL = "http://127.0.0.1:5000/traffic"
MODEL_NAME = "yolov8n.pt"  # modèle léger et rapide ; remplacer par 'yolov8s.pt' pour plus de précision
VEHICLE_CLASSES = {"car", "truck", "bus", "motorbike"}  # peut être étendu : "bicycle"
WINDOW_TITLE = "SR04 - Détection de trafic (HTTP)"
# -----------------------------------

# Chargement du modèle YOLO
print("Chargement du modèle YOLO... (le premier lancement peut prendre quelques secondes)")
model = YOLO(MODEL_NAME)

# --- Fenêtre principale Tkinter ---
root = tk.Tk()
root.title("SR04 - Client de trafic intelligent (HTTP)")
root.geometry("420x260")
root.resizable(False, False)

# --- Gestion du thread de détection ---
detector_thread = None

def run_detection(source_type: str, path: str | None = None):
    """
    Exécute la boucle de détection dans un thread séparé.
    source_type : "camera" ou "video"
    path : chemin du fichier vidéo si source_type == "video"
    """
    # Masquer la fenêtre principale pendant la détection
    root.withdraw()

    # Ouvrir la source vidéo
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

        # Détection YOLO
        results = model(frame, verbose=False)

        # Comptage et dessin des boîtes
        count = 0
        if results and len(results) > 0:
            r = results[0]
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                if label in VEHICLE_CLASSES:
                    count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Envoi du résultat au serveur Flask
        try:
            res = requests.post(SERVER_URL, json={"vehicle_count": count}, timeout=1.0)
            led = res.json().get("led", "red")
        except Exception:
            led = "red"

        # Dessin du feu tricolore à l’écran
        if led == "green":
            color = (0, 255, 0)
        elif led == "yellow":
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)
        cv2.circle(frame, (50, 50), 20, color, -1)

        # Affichage du nombre de véhicules
        cv2.putText(frame, f"Vehicles: {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Affiche la fenêtre OpenCV
        cv2.imshow(WINDOW_TITLE, frame)

        # Quitter avec la touche Échap
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    # Réafficher la fenêtre Tkinter après la détection
    root.deiconify()

def start_camera():
    """Lance la détection à partir de la caméra"""
    global detector_thread
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "La détection est déjà en cours.")
        return
    detector_thread = threading.Thread(target=run_detection, args=("camera",), daemon=True)
    detector_thread.start()

def upload_video():
    """Lance la détection à partir d’un fichier vidéo"""
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
    """Ferme proprement l’application"""
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()

# --- Interface graphique ---
tk.Label(root, text="SR04 Groupe 9 - Détection intelligente (HTTP)",
         font=("Segoe UI", 14, "bold")).pack(pady=18)

tk.Button(root, text="Ouvrir la caméra",
          command=start_camera, width=22, height=2, bg="#4CAF50", fg="white").pack(pady=6)

tk.Button(root, text="Choisir une vidéo",
          command=upload_video, width=22, height=2, bg="#2196F3", fg="white").pack(pady=6)

tk.Button(root, text="Quitter",
          command=exit_app, width=22, height=2, bg="#f44336", fg="white").pack(pady=12)

root.mainloop()
