# =========================================================
# SR04 Groupe 9 - Module de détection
# Fichier : client/detector.py
# Description :
#   Module réutilisable pour la détection de véhicules avec YOLOv8
#   - Détection des voitures, camions, bus, motos
#   - Dessin des cadres et du feu tricolore
#   - Option de sauvegarde de la latence de communication
# =========================================================

from ultralytics import YOLO
import cv2
import time
import os


class VehicleDetector:
    """
    Classe responsable du chargement du modèle YOLO et de la détection.
    """

    def __init__(self, model_name="yolov8n.pt", latency_file=None):
        """
        Initialise le détecteur avec un modèle YOLO.
        :param model_name: nom du modèle YOLO (ex: 'yolov8n.pt')
        :param latency_file: chemin du fichier CSV pour sauvegarder les latences
        """
        self.model_name = model_name
        self.latency_file = latency_file
        self.model = YOLO(model_name)
        self.vehicle_classes = {"car", "truck", "bus", "motorbike"}
        print(f"✅ Modèle YOLO chargé : {model_name}")

    def detect(self, frame):
        """
        Détecte les véhicules sur une image OpenCV.
        :param frame: image (numpy array)
        :return: tuple (nombre_de_véhicules, image_annotée)
        """
        results = self.model(frame, verbose=False)
        count = 0

        if results and len(results) > 0:
            r = results[0]
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                if label in self.vehicle_classes:
                    count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return count, frame

    def save_latency(self, latency_ms):
        """
        Sauvegarde la latence dans un fichier CSV.
        :param latency_ms: durée en millisecondes
        """
        if not self.latency_file:
            return
        os.makedirs(os.path.dirname(self.latency_file), exist_ok=True)
        with open(self.latency_file, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')},{latency_ms:.2f}\n")

    @staticmethod
    def draw_traffic_light(frame, led_color):
        """
        Dessine un feu tricolore sur l’image.
        :param frame: image OpenCV
        :param led_color: 'red', 'yellow' ou 'green'
        """
        if led_color == "green":
            color = (0, 255, 0)
        elif led_color == "yellow":
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)
        cv2.circle(frame, (50, 50), 20, color, -1)
