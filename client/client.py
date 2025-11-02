# =========================================================
# SR04 Group 9 Project
# File: client/client.py
# Description:
#   GUI-based YOLO vehicle detection client.
#   - Tkinter GUI: Open Camera / Upload Video
#   - YOLOv8 detection with bounding boxes and labels
#   - Sends vehicle count to Flask server
#   - Displays virtual traffic light (red/yellow/green)
# =========================================================

import cv2
import requests
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from ultralytics import YOLO

# ---------- Config ----------
SERVER_URL = "http://127.0.0.1:5000/traffic"
MODEL_NAME = "yolov8n.pt"  # small & fast; change to 'yolov8s.pt' for higher accuracy
VEHICLE_CLASSES = {"car", "truck", "bus", "motorbike"}  # extend if needed: "bicycle"
WINDOW_TITLE = "SR04 - YOLO Traffic Detection"
# ----------------------------

# Load YOLO model once
print("Loading YOLO model... (first time may take a few seconds)")
model = YOLO(MODEL_NAME)

# Global GUI root
root = tk.Tk()
root.title("SR04 Smart Traffic Client (YOLO)")
root.geometry("420x260")
root.resizable(False, False)

# Keep track of running detection thread
detector_thread = None

def run_detection(source_type: str, path: str | None = None):
    """
    Run detection loop in a background thread.
    source_type: "camera" or "video"
    path: video file path when source_type == "video"
    """
    # Hide GUI while detection window is displayed
    root.withdraw()

    # Open capture
    if source_type == "camera":
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera.")
            root.deiconify()
            return
    else:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot open selected video file.")
            root.deiconify()
            return

    while True:
        ret, frame = cap.read()
        if not ret:
            # Loop video
            if source_type == "video":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                break

        # Optional resize for speed
        # frame = cv2.resize(frame, (960, 540))

        # YOLO inference
        results = model(frame, verbose=False)

        # Count and draw boxes
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

        # Send to server
        try:
            res = requests.post(SERVER_URL, json={"vehicle_count": count}, timeout=1.0)
            led = res.json().get("led", "red")
        except Exception:
            led = "red"

        # Draw traffic light circle
        if led == "green":
            color = (0, 255, 0)
        elif led == "yellow":
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)
        cv2.circle(frame, (50, 50), 20, color, -1)

        # Display count text
        cv2.putText(frame, f"Vehicles: {count}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Show window
        cv2.imshow(WINDOW_TITLE, frame)

        # ESC to quit detection
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    # Show GUI again when detection ends
    root.deiconify()

def start_camera():
    global detector_thread
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "Detection is already running.")
        return
    detector_thread = threading.Thread(target=run_detection, args=("camera",), daemon=True)
    detector_thread.start()

def upload_video():
    global detector_thread
    if detector_thread and detector_thread.is_alive():
        messagebox.showinfo("Info", "Detection is already running.")
        return
    path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
    )
    if not path:
        return
    detector_thread = threading.Thread(target=run_detection, args=("video", path), daemon=True)
    detector_thread.start()

def exit_app():
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()

# --- GUI Layout ---
tk.Label(root, text="SR04 Group 9 - Smart Traffic (YOLO)",
         font=("Segoe UI", 14, "bold")).pack(pady=18)

tk.Button(root, text="Open Camera",
          command=start_camera, width=22, height=2, bg="#4CAF50", fg="white").pack(pady=6)

tk.Button(root, text="Upload Video",
          command=upload_video, width=22, height=2, bg="#2196F3", fg="white").pack(pady=6)

tk.Button(root, text="Exit",
          command=exit_app, width=22, height=2, bg="#f44336", fg="white").pack(pady=12)

root.mainloop()
