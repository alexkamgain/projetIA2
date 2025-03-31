import sqlite3
import bcrypt
import logging
from typing import Optional, Dict, Tuple
import pickle
from face_utils import register_face, compare_faces

DB_PATH = "face_auth.db"

def get_db_connection():
    """Établit une connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def init_db():
    """Initialise la structure de la base de données"""
    try:
        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password TEXT,
                    face_encoding BLOB,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Création de l'utilisateur admin par défaut
            try:
                hashed_pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    ("admin", "admin@example.com", hashed_pw)
                )
            except sqlite3.IntegrityError:
                pass
    except Exception as e:
        logging.error(f"Erreur d'initialisation de la base de données: {str(e)}")
        raise

def add_user(username: str, email: str, password: str, face_image: bytes) -> bool:
    """Ajoute un nouvel utilisateur standard"""
    try:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        face_encoding = register_face(face_image) if face_image else None
        
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password, face_encoding) VALUES (?, ?, ?, ?)",
                (username, email, hashed_pw, face_encoding)
            )
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"Le nom d'utilisateur existe déjà: {username}")
        return False
    except Exception as e:
        logging.error(f"Erreur lors de l'ajout d'utilisateur: {str(e)}")
        return False

def add_google_user(google_id: str, email: str, name: str) -> bool:
    """Ajoute un utilisateur via Google Auth"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, email, google_id) VALUES (?, ?, ?)",
                (name, email, google_id)
            )
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"Utilisateur Google déjà existant: {email}")
        return False
    except Exception as e:
        logging.error(f"Erreur lors de l'ajout d'utilisateur Google: {str(e)}")
        return False

def verify_user(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """Vérifie les identifiants de connexion standard"""
    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password IS NOT NULL", 
                (username,)
            ).fetchone()
            
        if user and bcrypt.checkpw(password.encode(), user['password']):
            return True, dict(user)
        return False, None
    except Exception as e:
        logging.error(f"Erreur de vérification d'utilisateur: {str(e)}")
        return False, None

def get_user_by_google_id(google_id: str) -> Optional[Dict]:
    """Récupère un utilisateur par son ID Google"""
    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE google_id = ?", 
                (google_id,)
            ).fetchone()
        return dict(user) if user else None
    except Exception as e:
        logging.error(f"Erreur de recherche Google: {str(e)}")
        return None

def get_user_by_face(image_bytes: bytes) -> Optional[Dict]:
    """Trouve un utilisateur par reconnaissance faciale"""
    try:
        if not image_bytes:
            return None
            
        with get_db_connection() as conn:
            users = conn.execute(
                "SELECT id, username, face_encoding FROM users WHERE face_encoding IS NOT NULL"
            ).fetchall()
            
            for user in users:
                match, confidence = compare_faces(user['face_encoding'], image_bytes)
                if match:
                    return dict(user)
                    
        return None
    except Exception as e:
        logging.error(f"Erreur de recherche faciale: {str(e)}")
        return None

def username_exists(username: str) -> bool:
    """Vérifie si un nom d'utilisateur existe déjà"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Erreur de vérification username: {str(e)}")
        return True

def face_exists(image_bytes: bytes) -> bool:
    """Vérifie si un visage similaire existe déjà"""
    try:
        if not image_bytes:
            return False
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT face_encoding FROM users WHERE face_encoding IS NOT NULL")
            existing_faces = cursor.fetchall()
            
            for (face_encoding,) in existing_faces:
                match, confidence = compare_faces(face_encoding, image_bytes)
                if match:
                    return True
        return False
    except Exception as e:
        logging.error(f"Erreur de vérification faciale: {str(e)}")
        return True