import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION DE L'APPLICATION
# ==========================================
# st.set_page_config DOIT être la première commande Streamlit
st.set_page_config(page_title="Tornado Tracker OSINT", page_icon="🌪️", layout="wide")

# L'API publique de la NOAA (Filtre strict sur les "Tornado Warnings")
NWS_API_URL = "https://api.weather.gov/alerts/active?event=Tornado%20Warning"

# ==========================================
# 🧠 FONCTIONS MOTEUR
# ==========================================
@st.cache_data(ttl=60) # Streamlit garde la donnée en mémoire 60 sec pour éviter de spammer l'API
def fetch_tornado_warnings():
    """Récupère les polygones d'alerte depuis la météo américaine."""
    try:
        # La NOAA exige un "User-Agent" pour savoir qui se connecte
        headers = {"User-Agent": "TornadoTrackerOSINT/1.0 (contact@example.com)"}
        response = requests.get(NWS_API_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Erreur de connexion aux satellites NOAA : {e}")
        return None

def create_tornado_map(data):
    """Génère la carte sombre avec les polygones de danger géométriques."""
    # On centre sur la "Tornado Alley" aux USA
    m = folium.Map(location=[38.0, -92.0], zoom_start=4, tiles="CartoDB dark_matter")

    if not data or 'features' not in data:
        return m

    for feature in data['features']:
        props = feature['properties']
        geom = feature.get('geometry')

        area = props.get('areaDesc', 'Zone inconnue')

        # Si l'API nous donne un polygone (La zone de frappe estimée)
        if geom and geom['type'] == 'Polygon':
            # Folium attend [Latitude, Longitude], mais le format GeoJSON donne [Longitude, Latitude]
            # On doit donc inverser les coordonnées pour chaque point du polygone
            coordinates = [[point[1], point[0]] for point in geom['coordinates'][0]]

            # On dessine le polygone d'alerte rouge sang
            folium.Polygon(
                locations=coordinates,
                color="#FF0000",
                weight=3,       # Épaisseur de la bordure
                fill=True,
                fill_color="#FF0000",
                fill_opacity=0.3, # Transparence pour voir la carte au travers
                tooltip=f"🚨 ZONE DE DANGER : {area}"
            ).add_to(m)

    return m

# ==========================================
# 🖥️ INTERFACE UTILISATEUR VISUELLE
# ==========================================
st.title("🌪️ Centre de Renseignement Météorologique")
st.markdown("Surveillance prédictive des cellules orageuses et suivi des **Tornado Warnings** (USA).")

# Bouton d'actualisation manuelle
if st.button("🔄 Forcer le balayage Radar"):
    st.rerun()

st.markdown("---")

# Récupération des données en temps réel
weather_data = fetch_tornado_warnings()

if weather_data:
    warnings = weather_data.get('features', [])
    active_count = len(warnings)

    # 1. LES COMPTEURS (METRICS)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Tornades Actives (Radar/Sol)", value=active_count)
    col2.metric(label="Source", value="NOAA (USA)")
    col3.metric(label="Dernier Balayage", value=datetime.now().strftime("%H:%M:%S"))

    st.markdown("<br>", unsafe_allow_html=True) # Espace visuel

    # 2. DISPOSITION EN DOUBLE COLONNE (Carte à gauche / Infos à droite)
    col_map, col_list = st.columns([2, 1]) # La carte prend 2/3 de l'écran

    with col_map:
        st.subheader("📡 Radar Spatial (Polygones de Danger)")
        radar_map = create_tornado_map(weather_data)
        # Affichage de la carte Folium DANS Streamlit
        st_folium(radar_map, width="100%", height=500, returned_objects=[])

    with col_list:
        st.subheader("🚨 Logs d'Alertes")
        if active_count == 0:
            st.success("Atmosphère stable. Aucune alerte tornade en cours.")
        else:
            # S'il y a des alertes, on crée des menus déroulants pour chacune
            for warning in warnings:
                props = warning['properties']
                zone = props.get('areaDesc', 'Zone')
                instruction = props.get('instruction', "Mettez-vous à l'abri immédiatement.")
                
                with st.expander(f"🔴 {zone}"):
                    st.write(f"**Gravité :** {props.get('severity')}")
                    st.write(f"**Certitude :** {props.get('certainty')}")
                    st.write("---")
                    st.markdown(f"<div style='color:#d9534f; font-size:12px;'>{instruction}</div>", unsafe_allow_html=True)