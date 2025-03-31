import face_recognition
import numpy as np
import cv2
import pickle
import logging
from typing import Optional, Tuple

def validate_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Valide et convertit une image en format RGB"""
    try:
        if not image_bytes or len(image_bytes) < 1024:
            raise ValueError("Image vide ou trop petite")
            
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Impossible de décoder l'image")
            
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        logging.error(f"Erreur de validation d'image: {str(e)}")
        return None

def register_face(image_bytes: bytes) -> Optional[bytes]:
    """Enregistre les caractéristiques faciales"""
    try:
        rgb_img = validate_image(image_bytes)
        if rgb_img is None:
            return None
            
        face_locations = face_recognition.face_locations(rgb_img)
        if len(face_locations) != 1:
            raise ValueError(f"{len(face_locations)} visages détectés - 1 requis")
            
        encodings = face_recognition.face_encodings(rgb_img, face_locations)
        if not encodings:
            raise ValueError("Impossible d'extraire les caractéristiques")
            
        return pickle.dumps(encodings[0])
    except Exception as e:
        logging.error(f"Erreur d'enregistrement facial: {str(e)}")
        return None

def compare_faces(db_encoding: bytes, new_image_bytes: bytes, threshold: float = 0.6) -> Tuple[bool, float]:
    """Compare deux visages et retourne la similarité"""
    try:
        if not db_encoding or not new_image_bytes:
            return False, 0.0
            
        known_encoding = pickle.loads(db_encoding)
        rgb_img = validate_image(new_image_bytes)
        if rgb_img is None:
            return False, 0.0
            
        face_locations = face_recognition.face_locations(rgb_img)
        if not face_locations:
            return False, 0.0
            
        new_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        if not new_encodings:
            return False, 0.0
            
        distances = face_recognition.face_distance([known_encoding], new_encodings[0])
        confidence = float(1 - distances[0])
        
        return confidence >= threshold, confidence
    except Exception as e:
        logging.error(f"Erreur de comparaison faciale: {str(e)}")
        return False, 0.0