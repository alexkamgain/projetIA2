# Documentation du Système d'Authentification Multi-Facteurs

## 📋 Table des Matières
- [1. Introduction](#1-introduction)
- [2. Prérequis](#2-prérequis)
- [3. Installation](#3-installation)
- [4. Configuration](#4-configuration)
- [5. Utilisation](#5-utilisation)
- [6. Architecture Technique](#6-architecture-technique)
- [7. Dépannage](#7-dépannage)
- [8. Sécurité](#8-sécurité)

## 1. Introduction
Système d'authentification sécurisé offrant 3 méthodes de connexion :
- 🔑 Authentification standard (email/mot de passe)
- 🖼️ Reconnaissance faciale
- 🔵 Connexion via Google OAuth

## 2. Prérequis

### Matériel
- 💻 Ordinateur avec webcam
- 🌐 Connexion Internet (pour OAuth)

### Logiciels
- Python 3.8+
- pip
- Bibliothèques :
  ```bash
  streamlit opencv-python face-recognition google-auth
3. Installation
Étapes rapides :
bash
Copy
git clone https://github.com/votre-repo/auth-system.git
cd auth-system
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python init_db.py
4. Configuration
Fichier config.py
python
Copy
GOOGLE_CLIENT_ID = "votre-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "votre-secret"
GOOGLE_REDIRECT_URI = "http://localhost:8501"  # Sans slash final