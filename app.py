import streamlit as st
import time
import logging
import cv2
import numpy as np
from database import (
    init_db, add_user, verify_user, 
    get_user_by_face, get_user_by_google_id,
    add_google_user, username_exists, face_exists
)
from face_utils import register_face, compare_faces
from config import setup_logging, get_google_auth_flow, GOOGLE_CLIENT_ID
from google.oauth2 import id_token
from google.auth.transport import requests

# Initialisation
setup_logging()
init_db()

# Configuration de la page
st.set_page_config(
    page_title="Authentification Multi-Facteurs",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS
st.markdown("""
<style>
    .google-btn {
        background-color: #4285F4 !important;
        color: white !important;
        padding: 10px 24px !important;
        border: none !important;
        border-radius: 4px !important;
        margin: 10px 0;
        width: 100%;
    }
    .camera-frame {
        border: 2px solid #4CAF50;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def check_camera_access():
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        cap.release()
        return True
    return False

def handle_login():
    st.subheader("Connexion Standard")
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter"):
            success, user = verify_user(username, password)
            if success:
                st.session_state.update({
                    'logged_in': True,
                    'username': username,
                    'user_id': user['id']
                })
                st.rerun()

def handle_registration():
    st.subheader("Création de Compte")
    with st.form("register_form"):
        new_username = st.text_input("Nom d'utilisateur")
        new_email = st.text_input("Email")
        new_password = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        face_image = st.camera_input("Capture faciale")
        
        if st.form_submit_button("S'inscrire"):
            # Validation et création du compte
            if new_password == confirm_password and not username_exists(new_username):
                face_bytes = face_image.getvalue() if face_image else None
                if add_user(new_username, new_email, new_password, face_bytes):
                    st.success("Compte créé avec succès!")
                    time.sleep(1)
                    st.rerun()

def handle_face_auth():
    st.subheader("Authentification Faciale")
    img = st.camera_input("Capturez votre visage")
    if img:
        user = get_user_by_face(img.getvalue())
        if user:
            st.session_state.update({
                'logged_in': True,
                'username': user['username'],
                'user_id': user['id']
            })
            st.rerun()

def handle_google_auth():
    if st.session_state.get('logged_in'):
        return
        
    st.subheader("Connexion Google")
    query_params = st.query_params.to_dict()
    
    # Nettoyage initial si pas de code
    if 'code' not in query_params:
        st.query_params.clear()
    else:
        try:
            with st.spinner("Connexion en cours..."):
                flow = get_google_auth_flow()
                flow.fetch_token(code=query_params['code'][0])
                id_info = id_token.verify_oauth2_token(
                    flow.credentials.id_token,
                    requests.Request(),
                    GOOGLE_CLIENT_ID
                )
                
                user = get_user_by_google_id(id_info['sub'])
                if not user:
                    username = id_info.get('name', id_info['email'].split('@')[0])
                    if add_google_user(id_info['sub'], id_info['email'], username):
                        user = get_user_by_google_id(id_info['sub'])
                
                if user:
                    st.session_state.update({
                        'logged_in': True,
                        'username': user['username'],
                        'user_id': user['id'],
                        'google_auth': True
                    })
                    st.query_params.clear()
                    time.sleep(0.5)
                    st.rerun()
                    
        except Exception as e:
            logging.error(f"Erreur Google: {str(e)}")
            st.query_params.clear()
    
    # Bouton de connexion
    flow = get_google_auth_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.markdown(f"""
    <a href="{auth_url}" target="_self">
        <button class="google-btn">Se connecter avec Google</button>
    </a>
    """, unsafe_allow_html=True)

def main():
    st.title("🔐 Système d'Authentification")
    
    if 'logged_in' not in st.session_state:
        st.session_state.update({
            'logged_in': False,
            'google_auth': False,
            'username': None
        })
    
    if not check_camera_access():
        st.warning("Autorisez l'accès à la caméra")
        st.stop()
    
    if not st.session_state['logged_in']:
        choice = st.sidebar.selectbox(
            "Menu",
            ["Connexion", "Inscription", "Authentification Faciale", "Connexion Google"]
        )
        if choice == "Connexion": handle_login()
        elif choice == "Inscription": handle_registration()
        elif choice == "Authentification Faciale": handle_face_auth()
        elif choice == "Connexion Google": handle_google_auth()
    else:
        st.sidebar.success(f"Connecté: {st.session_state['username']}")
        if st.sidebar.button("Déconnexion"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()