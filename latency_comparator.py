# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : latency_comparator.py
# Description :
#   Analyse et comparaison réseau avancée pour HTTP / WebSocket / MQTT
#   - Latence, Jitter, Bande passante, Énergie, Perte
#   - Interface Tkinter unifiée
# =========================================================



import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, Canvas, Frame

FILES = {
    "HTTP": "latency_http.csv",
    "WebSocket": "latency_ws.csv",
    "MQTT": "latency_mqtt.csv"
}


def analyze_latency(file_path, default_size=512):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, on_bad_lines="skip", engine="python")
        if "latency_ms" not in df.columns and "latency" in df.columns:
            df.rename(columns={"latency": "latency_ms"}, inplace=True)
        if "latency_ms" not in df.columns:
            return None
        df = df[(df["latency_ms"] > 0) & (df["latency_ms"] < 2000)]
        if len(df) < 2:
            return None

        latency_mean = df["latency_ms"].mean()
        jitter = df["latency_ms"].diff().abs().mean()
        if np.isnan(jitter) or jitter == 0:
            jitter = np.std(df["latency_ms"]) / 2
        msg_size = default_size
        bandwidth = (msg_size / (latency_mean / 1000)) / 1024
        energy = msg_size / 1024 / 1000 * 10
        loss = round(np.random.uniform(0.3, 1.2), 2)

        return {
            "latency": round(latency_mean, 2),
            "jitter": round(jitter, 2),
            "bandwidth": round(bandwidth, 2),
            "energy": round(energy, 3),
            "loss": loss,
        }
    except Exception:
        return None


def show_latency_gui():
    root = tk.Tk()
    root.title("Analyse des performances réseau - SR04 Groupe 9")
    root.geometry("1100x900")
    root.configure(bg="#F7F9FB")

    # --- zone scrollable pour éviter le masquage ---
    canvas = Canvas(root, bg="#F7F9FB")
    frame = Frame(canvas, bg="#F7F9FB")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", on_configure)

    # --- titre ---
    tk.Label(frame, text="📡 Comparaison des protocoles de communication",
             font=("Segoe UI", 16, "bold"), bg="#F7F9FB").pack(pady=10)

    # --- analyse ---
    stats = {}
    for proto, path in FILES.items():
        size = 512 if proto == "HTTP" else 70
        result = analyze_latency(path, size)
        if result:
            stats[proto] = result
    if not stats:
        messagebox.showerror("Erreur", "Aucun fichier valide trouvé.")
        root.destroy()
        return

    # --- table ---
    frame_table = ttk.Frame(frame)
    frame_table.pack(pady=10)
    columns = ("Protocole", "Latence (ms)", "Jitter (ms)", "Perte (%)", "Bande passante (kB/s)", "Énergie (kB/msg)")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=4)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=170, anchor="center")
    for proto, vals in stats.items():
        tree.insert("", "end", values=(proto, vals["latency"], vals["jitter"], vals["loss"], vals["bandwidth"], vals["energy"]))
    tree.pack()

    # --- graphique principal ---
    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    fig.subplots_adjust(wspace=0.4)
    axes[0].bar(stats.keys(), [v["latency"] for v in stats.values()], color="#4CAF50")
    axes[0].set_title("Latence moyenne (ms)")
    axes[1].bar(stats.keys(), [v["bandwidth"] for v in stats.values()], color="#2196F3")
    axes[1].set_title("Bande passante (kB/s)")
    axes[2].bar(stats.keys(), [v["energy"] for v in stats.values()], color="#FFC107")
    axes[2].set_title("Coût énergétique (kB/msg)")
    for ax in axes: ax.grid(alpha=0.3)

    canvas1 = FigureCanvasTkAgg(fig, master=frame)
    canvas1.draw()
    canvas1.get_tk_widget().pack(pady=15)

    # --- graphique secondaire ---
    fig2, ax2 = plt.subplots(1, 2, figsize=(10, 3.8))
    fig2.subplots_adjust(wspace=0.4)
    ax2[0].bar(stats.keys(), [v["jitter"] for v in stats.values()], color="#9C27B0")
    ax2[0].set_title("Variabilité de latence (Jitter ms)")
    ax2[1].bar(stats.keys(), [v["loss"] for v in stats.values()], color="#E91E63")
    ax2[1].set_title("Taux de perte simulé (%)")
    for ax in ax2: ax.grid(alpha=0.3)

    canvas2 = FigureCanvasTkAgg(fig2, master=frame)
    canvas2.draw()
    canvas2.get_tk_widget().pack(pady=15)

    tk.Label(frame, text="SR04 Groupe 9 — Analyse réseau avancée",
             font=("Segoe UI", 9, "italic"), bg="#F7F9FB").pack(pady=5)

    root.update()
    root.mainloop()


if __name__ == "__main__":
    show_latency_gui()


