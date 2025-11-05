# SR04 Groupe 9 - Système de détection de trafic intelligent

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

## Équipe du projet
**SR04 - Groupe 9**  
- **Maxime Gautrot**  
- **Jingjing Dai**  
- **Hassan Sahnoun**  

Encadré par :  
**Université de Technologie de Compiègne (UTC)**  
Module SR04 – Réseaux et Applications

---

## Licence
Projet académique – Usage strictement pédagogique.  
© 2025 UTC – Tous droits réservés.



