"""Private pilot access guard: local default, OIDC required for shared mode."""
import os
import streamlit as st


def require_access():
    mode=os.environ.get('ASTRASEC_MODE','local').strip()
    if mode=='local':return
    if mode!='private_pilot':
        st.error('Modo de despliegue no reconocido.');st.stop()
    try:
        allowed={email.strip().lower() for email in st.secrets['access']['allowed_emails'] if isinstance(email,str) and email.strip()}
        configured=bool(st.secrets['auth']['server_metadata_url'])
    except (KeyError,FileNotFoundError):
        allowed=set();configured=False
    if not configured or not allowed:
        st.error('Piloto privado bloqueado: configura OIDC y la lista de acceso antes de habilitarlo.');st.stop()
    if not st.user.is_logged_in:
        st.info('Acceso privado del equipo ELL.')
        if st.button('Iniciar sesión'):st.login()
        st.stop()
    email=st.user.get('email','').lower()
    if email not in allowed or st.user.get('email_verified') is not True:
        st.error('La identidad no tiene acceso aprobado o correo verificado.');st.stop()
    if st.sidebar.button('Cerrar sesión'):st.logout()
