# SR04 Groupe 9 - Système de détection de trafic intelligent

## Équipe du projet
**SR04 - Groupe 9**  
- **Maxime Gautrot**  
- **Jingjing Dai**  
- **Hassan Sahnoun**  

---


## Description du projet
Ce projet a été développé dans le cadre du module **SR04 - Réseaux et Applications** à l’**Université de Technologie de Compiègne (UTC)**.  
L’objectif est de concevoir un **système intelligent de gestion du trafic** basé sur l’intelligence artificielle (**YOLOv8**) et trois protocoles de communication différents :

- **HTTP** – communication client/serveur classique avec Flask  
- **WebSocket** – communication bidirectionnelle en temps réel  
- **MQTT** – communication légère adaptée à l’IoT (via Mosquitto)

---

## Architecture du projet
```
SR04_Group9Project/
│
├── client/
│   ├── client.py           # Client HTTP
│   ├── client_ws.py        # Client WebSocket
│   ├── client_mqtt.py      # Client MQTT
│
├── server/
│   ├── server.py           # Serveur HTTP (Flask)
│   ├── server_ws.py        # Serveur WebSocket (asyncio)
│   ├── server_mqtt.py      # Serveur MQTT (paho-mqtt)
│
├── run_all.py              # Interface graphique principale (sélection du mode)
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Description des modules

### 1. Détection YOLO (module commun `detector.py`)
- Contient la classe `VehicleDetector` utilisée par tous les clients (HTTP / WS / MQTT)
- Fonctionnalités :
  - Chargement du modèle **YOLOv8**
  - Détection des véhicules sur chaque image
  - Dessin des boîtes et du feu tricolore virtuel
  - Mesure et enregistrement des **latences** (CSV)

### 2. Clients
- `client_http.py` : envoie les détections via **requêtes HTTP** au serveur Flask  
- `client_ws.py` : communique avec le serveur via **WebSocket** (temps réel)  
- `client_mqtt.py` : publie les données sur un **broker MQTT** (Mosquitto)

### 3. Serveurs
- `server_http.py` : reçoit les requêtes POST, applique la logique du feu et renvoie la couleur  
- `server_ws.py` : maintient une connexion WebSocket bidirectionnelle  
- `server_mqtt.py` : écoute les messages du topic `traffic/vehicle_count` et publie `traffic/led`

### 4. Interface centrale `run_all.py`
- Interface Tkinter unifiée pour :
  - Lancer et arrêter les différents modes
  - Surveiller l’état des processus client/serveur
  - Visualiser les latences enregistrées (graphique)

---


## Installation et configuration

### 1️.Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

### 2️.Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3️.Installer Mosquitto (pour le mode MQTT)
Télécharger depuis :  
[https://mosquitto.org/download/](https://mosquitto.org/download/)  
Puis ajouter le dossier d’installation de **Mosquitto** dans la variable d’environnement `PATH`.

---

## Exécution du projet

### Lancer l’interface de contrôle :
```bash
python run_all.py
```

Une interface Tkinter s’ouvre, permettant de choisir le **mode de communication** :
- Mode 1 : HTTP  
- Mode 2 : WebSocket  
- Mode 3 : MQTT  

Chaque mode lance automatiquement le **serveur** et le **client** correspondants.

---

## Fonctionnalités principales
- Détection en temps réel des véhicules (voiture, bus, moto, camion) avec **YOLOv8**
- Transmission du nombre de véhicules au serveur
- Calcul dynamique du feu tricolore : 🔴 🟡 🟢  
- Affichage graphique du flux vidéo et du feu virtuel
- Compatibilité multi-protocole : HTTP / WS / MQTT
- Interface utilisateur simple et centralisée

---

## Résultats expérimentaux

Les tests ont été réalisés sur un ordinateur portable sous **Windows 11** avec :
- CPU : Intel Core i7  
- GPU : NVIDIA RTX 3050  
- Réseau local : Wi-Fi 5 GHz  

### Moyenne des latences mesurées :
| Protocole | Moyenne (ms) | Observation |
|------------|---------------|-------------|
| HTTP | ~120 ms | Stable mais moins réactif |
| WebSocket | ~70 ms | Très fluide et bidirectionnel |
| MQTT | ~60 ms | Le plus léger, idéal pour l’IoT |

### Interprétation :
- **HTTP** : simple mais légèrement plus lent car connexion recréée à chaque requête  
- **WebSocket** : très bon compromis entre performance et fiabilité  
- **MQTT** : optimal pour les environnements embarqués (ex. capteurs, Raspberry Pi)



## Technologies utilisées
| Composant | Technologie |
|------------|-------------|
| Détection IA | **YOLOv8** (Ultralytics) |
| Serveur HTTP | Flask |
| Serveur WebSocket | websockets |
| Serveur MQTT | paho-mqtt + Mosquitto |
| Interface graphique | Tkinter |
| Langage principal | Python 3.11 |
| OS testé | Windows 10 / 11 |

---

## Licence
Projet académique – Usage strictement pédagogique.  
© 2025 UTC – Tous droits réservés.



