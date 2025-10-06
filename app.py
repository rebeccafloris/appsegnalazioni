import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import datetime
import base64

# ===== CONFIG =====
st.set_page_config(page_title="Segnalazioni FS", page_icon="🚆", layout="wide")

# ===== FILE =====
if not os.path.exists("data"):
    os.makedirs("data")

path_utenti = "data/utenti.csv"
path_segnalazioni = "data/segnalazioni.csv"
stazioni_file = "data/stazioni_fs.csv"

# ===== CARICA DATI =====
if os.path.exists(path_utenti):
    utenti = pd.read_csv(path_utenti)
else:
    utenti = pd.DataFrame(columns=["username", "password"])
    utenti.to_csv(path_utenti, index=False)

if os.path.exists(path_segnalazioni):
    segnalazioni = pd.read_csv(path_segnalazioni)
else:
    segnalazioni = pd.DataFrame(columns=["utente", "stazione", "descrizione", "foto", "stato", "data"])
    segnalazioni.to_csv(path_segnalazioni, index=False)

if os.path.exists(stazioni_file):
    stazioni_df = pd.read_csv(stazioni_file, sep=';', encoding='utf-8')
else:
    st.warning(f"⚠️ File {stazioni_file} non trovato! Mettilo nella cartella data/")

# ===== FUNZIONI =====
def save_utenti():
    utenti.to_csv(path_utenti, index=False)

def save_segnalazioni():
    segnalazioni.to_csv(path_segnalazioni, index=False)

def create_user(username, password):
    if username in utenti["username"].values:
        st.error("Username già esistente!")
        return False
    utenti.loc[len(utenti)] = [username, password]
    save_utenti()
    st.success("Utente registrato!")
    return True

def login_user(username, password):
    user = utenti[(utenti["username"] == username) & (utenti["password"] == password)]
    if not user.empty:
        st.session_state["utente"] = username
        return True
    return False

def get_image_base64(photo_path):
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

# ===== SESSION STATE =====
if "utente" not in st.session_state:
    st.session_state["utente"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "next_page" not in st.session_state:
    st.session_state["next_page"] = None

# ===== HOME =====
def home_page():
    # Pulsanti Registrazione e Login sopra il banner
    col_reg, col_log = st.columns([1,1])
    with col_reg:
        if st.button("📝 Registrazione"):
            st.session_state["page"] = "registrazione"
    with col_log:
        if st.button("🔑 Login"):
            st.session_state["page"] = "login"

    st.markdown("<br>", unsafe_allow_html=True)

    # Banner principale
    st.markdown("""
        <div style="background: linear-gradient(90deg, #c8102e 0%, #a10d23 100%);
                    color: white; padding: 2rem; border-radius: 15px; text-align:center;">
            <h1>🚆 Segnalazioni FS</h1>
            <p>Servizio per inviare e gestire segnalazioni relative alle stazioni ferroviarie.</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Pulsanti principali sotto il banner
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("➕ Nuova Segnalazione"):
            if st.session_state["utente"] is None:
                st.session_state["next_page"] = "nuova"
                st.session_state["page"] = "login"
            else:
                st.session_state["page"] = "nuova"
    with col2:
        if st.button("📋 Visualizza Segnalazioni"):
            if st.session_state["utente"] is None:
                st.session_state["next_page"] = "visualizza"
                st.session_state["page"] = "login"
            else:
                st.session_state["page"] = "visualizza"

# ===== REGISTRAZIONE =====
def registrazione_page():
    st.subheader("Crea nuovo utente")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Registrati"):
        if create_user(username, password):
            st.session_state["page"] = "home"
    if st.button("🔙 Torna Home"):
        st.session_state["page"] = "home"

# ===== LOGIN =====
def login_page():
    st.subheader("Login")
    username = st.text_input("Username Login")
    password = st.text_input("Password Login", type="password")
    if st.button("Accedi"):
        if login_user(username, password):
            st.success(f"Login effettuato! Benvenuto {username}")
            # Dopo login vai direttamente alla pagina richiesta
            if st.session_state["next_page"]:
                st.session_state["page"] = st.session_state["next_page"]
                st.session_state["next_page"] = None
            else:
                st.session_state["page"] = "home"
        else:
            st.error("Username o password errati")
    if st.button("🔙 Torna Home"):
        st.session_state["page"] = "home"

# ===== NUOVA SEGNALAZIONE =====
def nuova_segnalazione():
    st.subheader("➕ Nuova Segnalazione")
    stazione_list = stazioni_df["Nome Stazione"].tolist() if not stazioni_df.empty else []
    stazione = st.selectbox("Seleziona Stazione FS", stazione_list)
    descrizione = st.text_area("Descrizione del problema")
    foto = st.file_uploader("Carica foto (opzionale)", type=["jpg","png","jpeg"])
    photo_path = ""
    if foto:
        if not os.path.exists("data/uploads"):
            os.makedirs("data/uploads")
        photo_path = os.path.join("data/uploads", foto.name)
        with open(photo_path, "wb") as f:
            f.write(foto.getbuffer())
        st.success("Foto caricata!")
    if st.button("Invia Segnalazione"):
        segnalazioni.loc[len(segnalazioni)] = [
            st.session_state["utente"],
            stazione,
            descrizione,
            photo_path,
            "In attesa",
            datetime.date.today()
        ]
        save_segnalazioni()
        st.success("Segnalazione inviata!")
    if st.button("🔙 Torna Home"):
        st.session_state["page"] = "home"

# ===== VISUALIZZA SEGNALAZIONI =====
def visualizza_segnalazioni():
    st.subheader("📋 Segnalazioni")
    df = segnalazioni
    st.dataframe(df)

    # Aggiorna stato
    if not df.empty:
        idx = st.number_input("ID segnalazione da modificare (indice tabella)", min_value=0, max_value=len(df)-1, step=1)
        nuovo_stato = st.selectbox("Aggiorna Stato", ["In attesa", "In lavorazione", "Risolta"])
        if st.button("Applica Modifiche"):
            segnalazioni.at[idx, "stato"] = nuovo_stato
            save_segnalazioni()
            st.success("Stato aggiornato!")

        # Elimina segnalazione
        if st.button("Elimina Segnalazione"):
            segnalazioni.drop(idx, inplace=True)
            segnalazioni.reset_index(drop=True, inplace=True)
            save_segnalazioni()
            st.success("Segnalazione eliminata!")

    # Mappa
    st.subheader("Mappa segnalazioni")
    m = folium.Map(location=[43.771,11.254], zoom_start=8)
    for _,row in df.iterrows():
        if row["stazione"] in stazioni_df["Nome Stazione"].values:
            stazione_info = stazioni_df[stazioni_df["Nome Stazione"]==row["stazione"]].iloc[0]
            folium.Marker(
                [stazione_info["Latitudine"], stazione_info["Longitudine"]],
                popup=f"{row['utente']} - {row['descrizione']} ({row['stato']})"
            ).add_to(m)
    st_folium(m, width=700, height=500)

    if st.button("🔙 Torna Home"):
        st.session_state["page"] = "home"

# ===== ROUTING =====
if st.session_state["page"] == "home":
    home_page()
elif st.session_state["page"] == "registrazione":
    registrazione_page()
elif st.session_state["page"] == "login":
    login_page()
elif st.session_state["page"] == "nuova":
    nuova_segnalazione()
elif st.session_state["page"] == "visualizza":
    visualizza_segnalazioni()
