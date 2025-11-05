# =========================================================
# SR04 Groupe 9 - Centre de contrôle final (HTTP / WS / MQTT)
# Description :
#   Interface unifiée pour contrôler les modes YOLO via HTTP, WebSocket ou MQTT
#   - Nettoyage automatique des processus
#   - Surveillance en arrière-plan
#   - Compatible avec toutes les versions client/serveur
# =========================================================

import tkinter as tk
import subprocess
import os
import signal
import threading
import time

# --- Chemins des fichiers ---
SERVER_HTTP = os.path.join("server", "server_http.py")
CLIENT_HTTP = os.path.join("client", "client_http.py")
SERVER_WS = os.path.join("server", "server_ws.py")
CLIENT_WS = os.path.join("client", "client_ws.py")
SERVER_MQTT = os.path.join("server", "server_mqtt.py")
CLIENT_MQTT = os.path.join("client", "client_mqtt.py")

# --- Fenêtre principale ---
root = tk.Tk()
root.title("SR04 - Smart Traffic Control Center")
root.geometry("550x420")
root.resizable(False, False)
root.configure(bg="#F7F9FB")

# --- Variables globales ---
selected_mode = tk.StringVar(value="HTTP")
status_text = tk.StringVar(value="🟢 En attente du lancement...")
server_process = None
client_process = None
stop_thread = False


# --- Fonctions utilitaires ---
def is_alive(proc):
    """Vérifie si un processus est encore en cours d’exécution"""
    try:
        return proc and proc.poll() is None
    except Exception:
        return False


def clean_dead_processes():
    """Nettoie les processus déjà terminés"""
    global server_process, client_process
    if server_process and not is_alive(server_process):
        server_process = None
    if client_process and not is_alive(client_process):
        client_process = None


# --- Lancer le projet ---
def launch_project():
    global server_process, client_process

    clean_dead_processes()  # Nettoyer les anciens processus

    if is_alive(server_process) or is_alive(client_process):
        status_text.set("Un projet est déjà en cours ! Fermez-le avant d’en lancer un autre.")
        return

    mode = selected_mode.get()
    if mode == "HTTP":
        server = SERVER_HTTP
        client = CLIENT_HTTP
        port = "5000"
    elif mode == "WebSocket":
        server = SERVER_WS
        client = CLIENT_WS
        port = "5001"
    elif mode == "MQTT":
        server = SERVER_MQTT
        client = CLIENT_MQTT
        port = "1883"
    else:
        status_text.set("Mode inconnu !")
        return

    try:
        server_process = subprocess.Popen(["python", server])
        time.sleep(1)
        client_process = subprocess.Popen(["python", client])
        status_text.set(f"Mode {mode} lancé sur le port {port}.")
    except Exception as e:
        status_text.set(f"Erreur de lancement : {e}")


# --- Arrêter le projet ---
def stop_project():
    global server_process, client_process
    try:
        if is_alive(client_process):
            client_process.terminate()
            client_process.wait(timeout=3)
        client_process = None
    except Exception:
        pass

    try:
        if is_alive(server_process):
            server_process.terminate()
            server_process.wait(timeout=3)
        server_process = None
    except Exception:
        pass

    status_text.set("🛑 Projet arrêté manuellement.")


# --- Surveillance automatique des processus ---
def monitor_processes():
    global stop_thread
    while not stop_thread:
        time.sleep(1)
        try:
            if server_process and not is_alive(server_process):
                status_text.set("🟡 Serveur arrêté (détecté automatiquement).")
                server_process = None
            if client_process and not is_alive(client_process):
                status_text.set("🟡 Client arrêté (détecté automatiquement).")
                client_process = None
        except Exception:
            pass


# --- Quitter le programme ---
def quit_app():
    global stop_thread
    stop_thread = True
    stop_project()
    root.destroy()


# --- Interface graphique ---
tk.Label(root, text="SR04 Group 9 - Smart Traffic Project",
         font=("Segoe UI", 16, "bold"), bg="#F7F9FB").pack(pady=20)

# --- Sélection du mode de communication ---
frame_mode = tk.LabelFrame(root, text="Choisir le mode de communication",
                           padx=10, pady=10, bg="#F7F9FB")
frame_mode.pack(padx=20, pady=10, fill="x")

tk.Radiobutton(frame_mode, text="Mode 1 : HTTP", variable=selected_mode,
               value="HTTP", bg="#F7F9FB", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
tk.Radiobutton(frame_mode, text="Mode 2 : WebSocket", variable=selected_mode,
               value="WebSocket", bg="#F7F9FB", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
tk.Radiobutton(frame_mode, text="Mode 3 : MQTT", variable=selected_mode,
               value="MQTT", bg="#F7F9FB", font=("Segoe UI", 11)).pack(anchor="w", padx=10)

# --- Boutons de contrôle ---
frame_buttons = tk.Frame(root, bg="#F7F9FB")
frame_buttons.pack(pady=20)

tk.Button(frame_buttons, text="▶ Lancer", command=launch_project,
          width=14, height=2, bg="#4CAF50", fg="white",
          font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=10)

tk.Button(frame_buttons, text="⏹️ Arrêter", command=stop_project,
          width=14, height=2, bg="#f44336", fg="white",
          font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=10)

# --- Zone d’état ---
tk.Label(root, textvariable=status_text, font=("Segoe UI", 11, "italic"),
         fg="#333", bg="#F7F9FB", wraplength=500, justify="center").pack(pady=10)

# --- Bouton Quitter ---
tk.Button(root, text="Quitter", command=quit_app, width=16,
          bg="#555", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

# --- Lancement du thread de surveillance ---
threading.Thread(target=monitor_processes, daemon=True).start()

root.mainloop()
