# =========================================================
# SR04 Groupe 9 - Centre de contrôle final (HTTP / WS / MQTT)
# Description :
#   Interface unifiée pour contrôler les modes YOLO via HTTP, WebSocket ou MQTT
#   - Nettoyage automatique des processus
#   - Surveillance en arrière-plan
#   - Visualisation des latences mesurées
# =========================================================

import tkinter as tk
import subprocess
import os
import signal
import threading
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tkinter import messagebox, Toplevel, Label, Button
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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
root.geometry("550x480")
root.resizable(False, False)
root.configure(bg="#F7F9FB")

# --- Variables globales ---
selected_mode = tk.StringVar(value="HTTP")
status_text = tk.StringVar(value="🟢 En attente du lancement...")
server_process = None
client_process = None
stop_thread = False


# =========================================================
# 🔹 Fonctions utilitaires de gestion de processus
# =========================================================
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


# =========================================================
# 🔹 Lancer / Arrêter le projet
# =========================================================
def launch_project():
    global server_process, client_process

    clean_dead_processes()

    if is_alive(server_process) or is_alive(client_process):
        status_text.set("⚠️ Un projet est déjà en cours ! Fermez-le avant d’en lancer un autre.")
        return

    mode = selected_mode.get()
    if mode == "HTTP":
        server, client, port = SERVER_HTTP, CLIENT_HTTP, "5000"
    elif mode == "WebSocket":
        server, client, port = SERVER_WS, CLIENT_WS, "5001"
    elif mode == "MQTT":
        server, client, port = SERVER_MQTT, CLIENT_MQTT, "1883"
    else:
        status_text.set("❌ Mode inconnu !")
        return

    try:
        server_process = subprocess.Popen(["python", server])
        time.sleep(1)
        client_process = subprocess.Popen(["python", client])
        status_text.set(f"✅ Mode {mode} lancé sur le port {port}.")
    except Exception as e:
        status_text.set(f"❌ Erreur de lancement : {e}")


def stop_project():
    """Arrête proprement les processus client et serveur"""
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


# =========================================================
# 🔹 Visualisation des latences
# =========================================================
# =========================================================
# 🔹 Visualisation des latences — version avec pertes réelles
# =========================================================
def show_latency_ui():
    """Affiche un tableau + graphiques combinés (avec pertes réelles)."""
    import numpy as np
    FILES = {
        "HTTP": "latency_http.csv",
        "WebSocket": "latency_ws.csv",
        "MQTT": "latency_mqtt.csv"
    }

    available = {name: path for name, path in FILES.items() if os.path.exists(path)}
    if not available:
        messagebox.showwarning("Aucun fichier", "Aucun fichier de latence trouvé.")
        return

    stats = {}
    for proto, file in available.items():
        try:
            df = pd.read_csv(file, on_bad_lines="skip", engine="python", dtype={"latency_ms": "float"})
            if "latency_ms" not in df.columns:
                continue

            # --- Ajout d'une taille simulée si manquante ---
            if "msg_size_bytes" not in df.columns:
                df["msg_size_bytes"] = 512 if proto == "HTTP" else 70  # taille moyenne d’un message

            # --- Nettoyage des données ---
            df = df[(df["latency_ms"] > 0) & (df["latency_ms"] < 2000)]
            if len(df) == 0:
                continue

            # --- Calculs principaux ---
            latencies = df["latency_ms"].to_numpy()
            timestamps = df["timestamp"].to_numpy()
            msg_sizes = df["msg_size_bytes"].to_numpy()

            mean_latency = np.mean(latencies)
            jitter = np.std(latencies)
            bandwidth = np.mean((msg_sizes / (latencies / 1000)) / 1024)
            energy = np.mean(msg_sizes / 1024)

            # --- Calcul du taux de perte réel ---
            if len(timestamps) > 1:
                diffs = np.diff(timestamps)
                mean_interval = np.mean(diffs)
                lost_count = np.sum(diffs > mean_interval * 3)
                real_loss_rate = (lost_count / len(diffs)) * 100
            else:
                real_loss_rate = 0.0

            stats[proto] = {
                "samples": len(df),
                "latency_ms": round(mean_latency, 2),
                "jitter_ms": round(jitter, 2),
                "real_loss_rate": round(real_loss_rate, 2),
                "bandwidth_kBps": round(bandwidth, 2),
                "energy_cost_kBmsg": round(energy, 4),
            }

        except Exception as e:
            print(f"⚠️ Erreur lecture {proto}: {e}")

    if not stats:
        messagebox.showwarning("Aucune donnée", "Aucune donnée exploitable trouvée.")
        return

    # --- Fenêtre Tkinter principale ---
    win = Toplevel(root)
    win.title("Analyse des performances réseau")
    win.geometry("1000x750")
    win.configure(bg="#F7F9FB")

    tk.Label(win, text="📊 Comparaison des protocoles de communication",
             font=("Segoe UI", 15, "bold"), bg="#F7F9FB").pack(pady=10)

    tk.Label(win, text="Analyse comparative : Latence, Jitter, Pertes réelles et Efficacité énergétique",
             font=("Segoe UI", 11, "italic"), bg="#F7F9FB").pack()

    # --- Tableau résumé ---
    frame_table = tk.Frame(win, bg="#F7F9FB")
    frame_table.pack(pady=5)

    headers = ["Protocole", "Échantillons", "Latence (ms)", "Jitter (ms)",
               "Pertes réelles (%)", "Bande passante (kB/s)", "Énergie (kB/msg)"]

    for c, h in enumerate(headers):
        tk.Label(frame_table, text=h, font=("Segoe UI", 11, "bold"),
                 width=18, bg="#F7F9FB").grid(row=0, column=c, padx=3, pady=2)

    for i, (proto, s) in enumerate(stats.items(), start=1):
        tk.Label(frame_table, text=proto, bg="#F7F9FB", font=("Segoe UI", 10)).grid(row=i, column=0)
        tk.Label(frame_table, text=s["samples"], bg="#F7F9FB").grid(row=i, column=1)
        tk.Label(frame_table, text=s["latency_ms"], bg="#F7F9FB").grid(row=i, column=2)
        tk.Label(frame_table, text=s["jitter_ms"], bg="#F7F9FB").grid(row=i, column=3)
        tk.Label(frame_table, text=s["real_loss_rate"], bg="#F7F9FB").grid(row=i, column=4)
        tk.Label(frame_table, text=s["bandwidth_kBps"], bg="#F7F9FB").grid(row=i, column=5)
        tk.Label(frame_table, text=s["energy_cost_kBmsg"], bg="#F7F9FB").grid(row=i, column=6)

    # --- Création du graphique combiné ---
    fig, axs = plt.subplots(2, 3, figsize=(14, 7))
    protocols = list(stats.keys())

    # Graphique 1 : Latence
    axs[0, 0].bar(protocols, [s["latency_ms"] for s in stats.values()],
                  color="#4CAF50", alpha=0.9)
    axs[0, 0].set_title("Latence moyenne (ms)")
    axs[0, 0].grid(alpha=0.3)

    # Graphique 2 : Bande passante
    axs[0, 1].bar(protocols, [s["bandwidth_kBps"] for s in stats.values()],
                  color="#2196F3", alpha=0.9)
    axs[0, 1].set_title("Bande passante (kB/s)")
    axs[0, 1].grid(alpha=0.3)

    # Graphique 3 : Énergie
    axs[0, 2].bar(protocols, [s["energy_cost_kBmsg"] for s in stats.values()],
                  color="#FFC107", alpha=0.9)
    axs[0, 2].set_title("Coût énergétique (kB/msg)")
    axs[0, 2].grid(alpha=0.3)

    # Graphique 4 : Jitter
    axs[1, 0].bar(protocols, [s["jitter_ms"] for s in stats.values()],
                  color="#9C27B0", alpha=0.9)
    axs[1, 0].set_title("Variabilité de latence (Jitter ms)")
    axs[1, 0].grid(alpha=0.3)

    # Graphique 5 : Pertes réelles
    axs[1, 1].bar(protocols, [s["real_loss_rate"] for s in stats.values()],
                  color="#E91E63", alpha=0.9)
    axs[1, 1].set_title("Taux de perte réel (%)")
    axs[1, 1].grid(alpha=0.3)

    # Cacher le dernier sous-plot vide
    axs[1, 2].axis("off")

    fig.tight_layout()

    # --- Intégration dans Tkinter ---
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=15)

    tk.Button(win, text="Fermer", command=win.destroy,
              bg="#555", fg="white", font=("Segoe UI", 10, "bold"), width=12).pack(pady=10)






# =========================================================
# 🔹 Surveillance automatique des processus
# =========================================================
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


# =========================================================
# 🔹 Quitter le programme
# =========================================================
def quit_app():
    global stop_thread
    stop_thread = True
    stop_project()
    root.destroy()


# =========================================================
# 🔹 Interface graphique
# =========================================================
tk.Label(root, text="SR04 Group 9 - Smart Traffic Project",
         font=("Segoe UI", 16, "bold"), bg="#F7F9FB").pack(pady=20)

# --- Sélection du mode ---
frame_mode = tk.LabelFrame(root, text="Choisir le mode de communication",
                           padx=10, pady=10, bg="#F7F9FB")
frame_mode.pack(padx=20, pady=10, fill="x")

tk.Radiobutton(frame_mode, text="Mode 1 : HTTP", variable=selected_mode,
               value="HTTP", bg="#F7F9FB", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
tk.Radiobutton(frame_mode, text="Mode 2 : WebSocket", variable=selected_mode,
               value="WebSocket", bg="#F7F9FB", font=("Segoe UI", 11)).pack(anchor="w", padx=10)
tk.Radiobutton(frame_mode, text="Mode 3 : MQTT", variable=selected_mode,
               value="MQTT", bg="#F7F9FB", font=("Segoe UI", 11)).pack(anchor="w", padx=10)

# --- Boutons principaux ---
frame_buttons = tk.Frame(root, bg="#F7F9FB")
frame_buttons.pack(pady=20)

tk.Button(frame_buttons, text="▶ Lancer", command=launch_project,
          width=14, height=2, bg="#4CAF50", fg="white",
          font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=10)

tk.Button(frame_buttons, text="⏹️ Arrêter", command=stop_project,
          width=14, height=2, bg="#f44336", fg="white",
          font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=10)

# --- Bouton de visualisation des latences ---
tk.Button(root, text="📊 Voir les latences", command=show_latency_ui,
          width=22, height=2, bg="#FFC107", fg="black",
          font=("Segoe UI", 10, "bold")).pack(pady=5)

# --- Zone d’état ---
tk.Label(root, textvariable=status_text, font=("Segoe UI", 11, "italic"),
         fg="#333", bg="#F7F9FB", wraplength=500, justify="center").pack(pady=10)

# --- Bouton Quitter ---
tk.Button(root, text="Quitter", command=quit_app, width=16,
          bg="#555", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

# --- Lancement du thread de surveillance ---
threading.Thread(target=monitor_processes, daemon=True).start()

root.mainloop()
