# =========================================================
# SR04 Groupe 9 - Projet
# Fichier : latency_comparator.py
# Description :
#   Compare les latences mesurées pour les trois protocoles :
#   HTTP, WebSocket et MQTT.
#   - Lit les fichiers CSV générés pendant les tests
#   - Affiche un graphique comparatif
#   - Calcule la latence moyenne pour chaque protocole
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import os

# --- Fichiers à comparer ---
FILES = {
    "HTTP": "latency_http.csv",
    "WebSocket": "latency_ws.csv",
    "MQTT": "latency_mqtt.csv"
}

# --- Vérifie quels fichiers existent ---
available = {name: path for name, path in FILES.items() if os.path.exists(path)}

if not available:
    print("Aucun fichier de latence trouvé dans le répertoire courant.")
    print("Assurez-vous d’avoir exécuté les trois clients avant.")
    exit()

data = {}
means = {}

# --- Lecture et nettoyage des données ---
for proto, file in available.items():
    df = pd.read_csv(file)
    if "latency_ms" not in df.columns:
        print(f"Le fichier {file} ne contient pas de colonne 'latency_ms'.")
        continue
    # Supprime les valeurs aberrantes (>2000 ms)
    df = df[df["latency_ms"] < 2000]
    data[proto] = df["latency_ms"].reset_index(drop=True)
    means[proto] = round(df["latency_ms"].mean(), 2)

# --- Vérifie si au moins une série est valide ---
if not data:
    print("Aucun fichier valide trouvé.")
    exit()

# --- Affiche les moyennes dans la console ---
print("\n📊 Résumé des latences moyennes (en millisecondes) :")
for proto, mean in means.items():
    print(f"   {proto:<10} →  {mean} ms")

# --- Graphique 1 : évolution temporelle ---
plt.figure(figsize=(10, 5))
for proto, series in data.items():
    plt.plot(series, label=f"{proto} (moyenne = {means[proto]} ms)", linewidth=1.6)

plt.title("Comparaison temporelle des latences — SR04 Groupe 9", fontsize=13)
plt.xlabel("Itération / message envoyé")
plt.ylabel("Latence (ms)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# --- Graphique 2 : moyenne comparative ---
plt.figure(figsize=(6, 4))
plt.bar(means.keys(), means.values(), color=["#4CAF50", "#2196F3", "#FFC107"])
plt.title("Latence moyenne par protocole", fontsize=13)
plt.ylabel("Latence moyenne (ms)")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
