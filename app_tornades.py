import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone
import time
import json
import csv
import io
import math
import html as html_mod
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==========================================
# 📧  EMAIL CONFIG
# ==========================================
EMAIL_SENDER   = "alexbailly82@gmail.com"
EMAIL_RECEIVER = "alexbailly82@gmail.com"
EMAIL_PASSWORD = "ojfwwjozkjxjlszn"

EMAIL_TRIGGER_EVENTS = [
    "Tornado Warning",
    "Tornado Emergency",
]

def send_alert_email(new_alerts):
    if not new_alerts:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌪️ VORTEX ALERT — {len(new_alerts)} nouvelle(s) alerte(s) tornade"
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECEIVER

        plain_lines = [f"VORTEX — Severe Weather Intelligence\n{'='*45}"]
        for a in new_alerts:
            plain_lines.append(
                f"\n⚠ {a['event']}\n"
                f"Zone     : {a['area']}\n"
                f"Sévérité : {a['severity']} | Certitude : {a['certainty']}\n"
                f"Heure    : {a['onset']}\n"
                f"Instructions : {a['instruction'][:200]}\n"
                f"{'-'*45}"
            )
        plain_lines.append("\nSource : NOAA / National Weather Service (USA)")
        plain_text = "\n".join(plain_lines)

        alert_rows = ""
        for a in new_alerts:
            color = "#FF3B30" if a["event"] == "Tornado Emergency" else "#FF6B35"
            alert_rows += f"""
            <div style="background:#0A0F1E;border-left:4px solid {color};border-radius:8px;
                        padding:16px 20px;margin-bottom:16px;font-family:monospace;">
              <div style="color:{color};font-size:11px;letter-spacing:.1em;
                          text-transform:uppercase;margin-bottom:8px;">{a['event']}</div>
              <div style="color:#E2E8F0;font-size:16px;font-weight:600;margin-bottom:12px;">{a['area']}</div>
              <table style="width:100%;font-size:13px;color:#94A3B8;border-collapse:collapse;">
                <tr><td style="padding:4px 0;width:120px;">Sévérité</td>
                    <td style="color:#E2E8F0;">{a['severity']}</td></tr>
                <tr><td style="padding:4px 0;">Certitude</td>
                    <td style="color:#E2E8F0;">{a['certainty']}</td></tr>
                <tr><td style="padding:4px 0;">Heure UTC</td>
                    <td style="color:#E2E8F0;">{a['onset']}</td></tr>
              </table>
              <div style="margin-top:12px;padding:10px 14px;background:#050810;border-radius:6px;
                          font-size:12px;color:#CBD5E1;line-height:1.6;">
                {a['instruction'][:300]}{'…' if len(a['instruction']) > 300 else ''}
              </div>
            </div>"""

        html_body = f"""
        <html><body style="background:#050810;margin:0;padding:24px;font-family:'Segoe UI',sans-serif;">
          <div style="max-width:600px;margin:0 auto;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;">
              <div style="background:linear-gradient(135deg,#FF3B30,#FF6B35);
                          border-radius:10px;width:40px;height:40px;display:flex;
                          align-items:center;justify-content:center;font-size:20px;">🌪</div>
              <div>
                <div style="color:#FFFFFF;font-size:18px;font-weight:700;letter-spacing:.12em;">VORTEX</div>
                <div style="color:#4A6FA5;font-size:10px;letter-spacing:.1em;">SEVERE WEATHER INTELLIGENCE</div>
              </div>
            </div>
            <div style="color:#FF3B30;font-size:13px;font-family:monospace;
                        letter-spacing:.1em;margin-bottom:16px;">
              ● {len(new_alerts)} NOUVELLE(S) ALERTE(S) DÉTECTÉE(S)
            </div>
            {alert_rows}
            <div style="margin-top:24px;padding-top:16px;border-top:1px solid #0F1E38;
                        font-size:11px;color:#374151;font-family:monospace;">
              Source : NOAA / National Weather Service (USA) · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
            </div>
          </div>
        </body></html>"""

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        return True
    except Exception as e:
        st.toast(f"Erreur email : {e}", icon="❌")
        return False

# ==========================================
# ⚙️  PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="VORTEX · Severe Weather Intelligence",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 🎨  CUSTOM CSS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
    background: #050810 !important;
    color: #E2E8F0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

    header[data-testid="stHeader"]  { display: none !important; }
[data-testid="stToolbar"]       { display: none !important; }
[data-testid="stDecoration"]    { display: none !important; }
[data-testid="stStatusWidget"]  { display: none !important; }
#MainMenu                        { display: none !important; }
footer                           { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stSidebar"] { background: #080D1A !important; border-right: 1px solid #1A2540; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080D1A; }
::-webkit-scrollbar-thumb { background: #1E3A5F; border-radius: 2px; }

.vortex-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    height: 64px;
    background: #080D1A;
    border-bottom: 1px solid #0F1E38;
    position: sticky;
    top: 0;
    z-index: 100;
}
.vortex-logo { display: flex; align-items: center; gap: 12px; }
.vortex-logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #FF3B30, #FF6B35);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.vortex-logo-text { font-size: 18px; font-weight: 700; letter-spacing: 0.15em; color: #FFFFFF; }
.vortex-logo-sub { font-size: 10px; color: #4A6FA5; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.1em; }
.vortex-status { display: flex; align-items: center; gap: 8px; font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #4A6FA5; }
.vortex-status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 8px #22C55E;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.vortex-body { padding: 1.5rem 2rem; display: flex; flex-direction: column; gap: 1.5rem; }

.metric-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.metric-card {
    background: #080D1A;
    border: 1px solid #0F1E38;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }
.metric-card.danger::before  { background: linear-gradient(90deg, #FF3B30, transparent); }
.metric-card.warning::before { background: linear-gradient(90deg, #F59E0B, transparent); }
.metric-card.info::before    { background: linear-gradient(90deg, #3B82F6, transparent); }
.metric-card.success::before { background: linear-gradient(90deg, #22C55E, transparent); }
.metric-card.neutral::before { background: linear-gradient(90deg, #6B7280, transparent); }

.metric-label { font-size: 10px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.12em; color: #4A6FA5; text-transform: uppercase; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; line-height: 1; color: #FFFFFF; }
.metric-value.danger  { color: #FF3B30; }
.metric-value.warning { color: #F59E0B; }
.metric-value.success { color: #22C55E; }
.metric-sub { font-size: 11px; color: #4A6FA5; margin-top: 4px; font-family: 'JetBrains Mono', monospace; }

.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-title { font-size: 11px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.15em; color: #4A6FA5; text-transform: uppercase; }
.section-badge { font-size: 10px; font-family: 'JetBrains Mono', monospace; padding: 3px 10px; border-radius: 20px; background: #0F1E38; color: #4A6FA5; border: 1px solid #1A2540; }
.section-badge.live { background: rgba(255, 59, 48, 0.1); color: #FF3B30; border-color: rgba(255, 59, 48, 0.3); }

.panel { background: #080D1A; border: 1px solid #0F1E38; border-radius: 16px; padding: 1.25rem; height: 100%; }

.alert-row {
    display: flex; align-items: flex-start; gap: 12px; padding: 12px 0;
    border-bottom: 1px solid #0A1628; cursor: pointer; transition: background 0.15s;
    border-radius: 8px; padding-left: 8px; margin-left: -8px;
}
.alert-row:hover { background: rgba(255,255,255,0.02); }
.alert-row:last-child { border-bottom: none; }

.alert-sev-bar { width: 3px; min-height: 50px; border-radius: 2px; align-self: stretch; flex-shrink: 0; }
.sev-extreme { background: #FF3B30; box-shadow: 0 0 6px rgba(255,59,48,0.5); }
.sev-severe  { background: #F59E0B; }
.sev-moderate{ background: #3B82F6; }
.sev-minor   { background: #22C55E; }
.sev-expired { background: #374151; }

.alert-content { flex: 1; min-width: 0; }
.alert-zone { font-size: 13px; font-weight: 600; color: #E2E8F0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alert-type { font-size: 11px; font-family: 'JetBrains Mono', monospace; color: #4A6FA5; margin-top: 2px; }
.alert-meta { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
.alert-tag { font-size: 10px; padding: 2px 7px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; border: 1px solid; }
.tag-extreme  { background: rgba(255,59,48,0.1); color: #FF6B6B; border-color: rgba(255,59,48,0.3); }
.tag-severe   { background: rgba(245,158,11,0.1); color: #FBB040; border-color: rgba(245,158,11,0.3); }
.tag-moderate { background: rgba(59,130,246,0.1); color: #60A5FA; border-color: rgba(59,130,246,0.3); }
.tag-info     { background: rgba(100,116,139,0.1); color: #94A3B8; border-color: rgba(100,116,139,0.3); }
.alert-time { font-size: 10px; font-family: 'JetBrains Mono', monospace; color: #374151; margin-top: 4px; }

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.filter-chip { font-size: 11px; font-family: 'JetBrains Mono', monospace; padding: 5px 12px; border-radius: 6px; border: 1px solid #1A2540; background: #0A1220; color: #4A6FA5; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.filter-chip.active { background: #0F1E38; border-color: #3B82F6; color: #60A5FA; }
.filter-chip.danger.active { border-color: #FF3B30; color: #FF6B6B; background: rgba(255,59,48,0.08); }

.refresh-bar { background: #0A1220; border: 1px solid #0F1E38; border-radius: 10px; padding: 10px 16px; display: flex; align-items: center; gap: 12px; }
.refresh-label { font-size: 11px; font-family: 'JetBrains Mono', monospace; color: #4A6FA5; flex-shrink: 0; }
.progress-track { flex: 1; height: 3px; background: #0F1E38; border-radius: 2px; overflow: hidden; }
.progress-fill-bar { height: 3px; border-radius: 2px; background: linear-gradient(90deg, #3B82F6, #60A5FA); transition: width 1s linear; }
.refresh-countdown { font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #3B82F6; min-width: 40px; text-align: right; }

.timeline-container { display: flex; align-items: flex-end; gap: 3px; height: 40px; padding: 4px 0; }
.timeline-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.timeline-bar { width: 100%; border-radius: 2px 2px 0 0; min-height: 2px; transition: opacity 0.2s; }
.timeline-bar:hover { opacity: 0.7; }
.timeline-hour { font-size: 9px; font-family: 'JetBrains Mono', monospace; color: #374151; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem 1rem; color: #374151; text-align: center; gap: 12px; }
.empty-icon { font-size: 40px; opacity: 0.4; }
.empty-text { font-size: 14px; color: #4A6FA5; }

.detail-section { margin-bottom: 16px; }
.detail-label { font-size: 10px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.1em; color: #4A6FA5; text-transform: uppercase; margin-bottom: 4px; }
.detail-value { font-size: 13px; color: #CBD5E1; line-height: 1.5; }
.detail-instruction { font-size: 12px; color: #94A3B8; line-height: 1.6; padding: 10px 12px; background: rgba(255,59,48,0.05); border-left: 2px solid rgba(255,59,48,0.4); border-radius: 0 6px 6px 0; }

[data-testid="stMetric"] { display: none !important; }
div[data-testid="column"] > div { height: 100%; }
.stButton > button {
    background: #0A1220 !important; color: #60A5FA !important;
    border: 1px solid #1A2540 !important; border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important;
    letter-spacing: 0.05em !important; transition: all 0.15s !important; width: 100% !important;
}
.stButton > button:hover { background: #0F1E38 !important; border-color: #3B82F6 !important; }
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: #080D1A !important; border: 1px solid #1A2540 !important;
    border-radius: 8px !important; color: #E2E8F0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stSlider > div > div > div { background: #3B82F6 !important; }
[data-testid="stSlider"] label { color: #4A6FA5 !important; font-size: 11px !important; font-family: 'JetBrains Mono', monospace !important; letter-spacing: 0.1em !important; }
[data-testid="stExpander"] { background: #0A1220 !important; border: 1px solid #0F1E38 !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary { color: #94A3B8 !important; font-size: 12px !important; }
.stAlert { border-radius: 10px !important; border: none !important; }
[data-testid="stDownloadButton"] > button { background: rgba(34,197,94,0.08) !important; color: #22C55E !important; border: 1px solid rgba(34,197,94,0.3) !important; }
[data-testid="stDownloadButton"] > button:hover { background: rgba(34,197,94,0.15) !important; }
div[data-testid="stHorizontalBlock"] { gap: 1rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌐  API ENDPOINTS
# ==========================================
NWS_EVENTS = [
    "Tornado Warning",
    "Tornado Watch",
    "Severe Thunderstorm Warning",
    "Flash Flood Warning",
    "Tornado Emergency",
]

SEVERITY_ORDER = {
    "Extreme":  0,
    "Severe":   1,
    "Moderate": 2,
    "Minor":    3,
    "Unknown":  4,
}

SEV_COLORS = {
    "Extreme":  ("#FF3B30", "sev-extreme",  "tag-extreme"),
    "Severe":   ("#F59E0B", "sev-severe",   "tag-severe"),
    "Moderate": ("#3B82F6", "sev-moderate", "tag-moderate"),
    "Minor":    ("#22C55E", "sev-minor",    "tag-info"),
    "Unknown":  ("#374151", "sev-expired",  "tag-info"),
}

EVENT_COLORS = {
    "Tornado Warning":             "#FF3B30",
    "Tornado Emergency":           "#FF0000",
    "Tornado Watch":               "#F59E0B",
    "Severe Thunderstorm Warning": "#F59E0B",
    "Flash Flood Warning":         "#3B82F6",
}

# ==========================================
# 🧠  DATA FETCHING
# ==========================================
@st.cache_data(ttl=60)
def fetch_all_alerts():
    all_features = []
    headers = {"User-Agent": "VORTEX-SWI/2.0 (ops@vortex-swi.io)"}
    for event in NWS_EVENTS:
        try:
            url = f"https://api.weather.gov/alerts/active?event={requests.utils.quote(event)}"
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            for f in data.get("features", []):
                f["_event_type"] = event
            all_features.extend(data.get("features", []))
        except Exception:
            pass
    seen = set()
    unique = []
    for f in all_features:
        fid = f.get("id", "") or f["properties"].get("id", "")
        if fid not in seen:
            seen.add(fid)
            unique.append(f)
    return unique

def parse_time(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def format_time_ago(dt):
    if not dt:
        return "—"
    now = datetime.now(timezone.utc)
    diff = now - dt
    mins = int(diff.total_seconds() / 60)
    if mins < 1:  return "just now"
    if mins < 60: return f"{mins}m ago"
    hrs = mins // 60
    if hrs < 24:  return f"{hrs}h ago"
    return f"{hrs//24}d ago"

# ==========================================
# 📍  SPC TORNADO REPORTS (trajectoires confirmées)
# ==========================================
SPC_REPORTS_URL = "https://www.spc.noaa.gov/climo/reports/today_filtered.csv"

@st.cache_data(ttl=300)  # refresh toutes les 5 min
def fetch_spc_tornado_reports():
    """Récupère uniquement les tornades confirmées SPC du jour."""
    try:
        r = requests.get(SPC_REPORTS_URL, timeout=10,
                         headers={"User-Agent": "VORTEX-SWI/2.0"})
        r.raise_for_status()
        reports = []
        lines = r.text.strip().split('\n')
        in_tornado_section = False
        for line in lines:
            line = line.strip()
            if line.upper() == "TORNADO":
                in_tornado_section = True
                continue
            if line.upper() in ("HAIL", "WIND"):
                in_tornado_section = False
                continue
            if in_tornado_section and line.lower().startswith("time"):
                continue
            if in_tornado_section and line:
                parts = line.split(',')
                if len(parts) >= 7:
                    try:
                        lat = float(parts[5].strip())
                        lon = float(parts[6].strip())
                        if lat == 0 and lon == 0:
                            continue
                        # Parse heure pour tri chronologique
                        t_str = parts[0].strip()
                        reports.append({
                            'time':     t_str,
                            'f_scale':  parts[1].strip(),
                            'location': parts[2].strip(),
                            'county':   parts[3].strip(),
                            'state':    parts[4].strip(),
                            'lat':      lat,
                            'lon':      lon,
                            'comments': parts[7].strip() if len(parts) > 7 else '',
                        })
                    except (ValueError, IndexError):
                        pass
        # Trie par heure pour avoir les trajectoires dans l'ordre
        reports.sort(key=lambda x: x['time'])
        return reports
    except Exception:
        return []

def group_spc_trajectories(reports, max_dist_km=150, max_time_min=60):
    """
    Regroupe les rapports SPC proches dans le temps et l'espace
    pour reconstruire des trajectoires de tornades distinctes.
    Retourne une liste de groupes (chaque groupe = une tornade).
    """
    if not reports:
        return []

    def time_to_min(t_str):
        try:
            h, m = int(t_str[:2]), int(t_str[2:4])
            return h * 60 + m
        except Exception:
            return 0

    def dist_km(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    groups = []
    used = set()

    for i, rep in enumerate(reports):
        if i in used:
            continue
        group = [rep]
        used.add(i)
        for j, other in enumerate(reports):
            if j in used or j == i:
                continue
            dt = abs(time_to_min(rep['time']) - time_to_min(other['time']))
            dd = dist_km(rep['lat'], rep['lon'], other['lat'], other['lon'])
            if dt <= max_time_min and dd <= max_dist_km:
                group.append(other)
                used.add(j)
        groups.append(sorted(group, key=lambda x: x['time']))

    return groups

# ==========================================
# 🌪️  TORNADO LIVE POSITION & TRAJECTORY
# ==========================================

def compute_centroid(coords):
    """Calcule le centroïde d'un polygone GeoJSON → (lat, lon)."""
    lats = [p[1] for p in coords]
    lons = [p[0] for p in coords]
    return sum(lats) / len(lats), sum(lons) / len(lons)

def extract_tornado_positions(features):
    """
    Extrait la position approximative (centroïde du polygone)
    de chaque Tornado Warning / Emergency actif.
    """
    positions = {}
    for f in features:
        props = f["properties"]
        event = props.get("event", "")
        if event not in ("Tornado Warning", "Tornado Emergency"):
            continue
        geom = f.get("geometry")
        if geom and geom.get("type") == "Polygon":
            alert_id = props.get("id", "") or f.get("id", "")
            lat, lon = compute_centroid(geom["coordinates"][0])
            positions[alert_id] = {
                'lat':      lat,
                'lon':      lon,
                'event':    event,
                'area':     props.get("areaDesc", ""),
                'severity': props.get("severity", ""),
                'onset':    props.get("onset", ""),
            }
    return positions

def update_trajectories(current_positions):
    """
    Ajoute le point courant dans l'historique de chaque tornade.
    Conserve les 20 dernières positions par alerte.
    """
    if "tornado_trajectories" not in st.session_state:
        st.session_state.tornado_trajectories = {}

    for alert_id, pos in current_positions.items():
        hist = st.session_state.tornado_trajectories.get(alert_id, [])
        # N'ajoute que si la position a changé (ou premier point)
        if not hist or (hist[-1][0] != pos['lat'] or hist[-1][1] != pos['lon']):
            ts = datetime.now(timezone.utc).strftime("%H:%M")
            hist.append((pos['lat'], pos['lon'], ts))
        st.session_state.tornado_trajectories[alert_id] = hist[-20:]

# ==========================================
# 🗺️  MAP BUILDER  (avec position live + trajectoire + SPC)
# ==========================================
def build_map(features, show_events, tornado_positions, trajectories, spc_groups):
    m = folium.Map(
        location=[38.0, -95.0],
        zoom_start=4,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Dark Matter",
        max_zoom=19,
    ).add_to(m)

    # ── POLYGONES D'ALERTE (zones rouges) ────────────────────────
    count = 0
    for f in features:
        props = f["properties"]
        event = props.get("event", "")
        if event not in show_events:
            continue
        geom        = f.get("geometry")
        sev         = props.get("severity", "Unknown")
        area        = props.get("areaDesc", "Unknown zone")
        headline    = props.get("headline", event)
        instruction = props.get("instruction", "") or ""
        color       = EVENT_COLORS.get(event, "#6B7280")

        if geom and geom.get("type") == "Polygon":
            coords = [[p[1], p[0]] for p in geom["coordinates"][0]]
            popup_html = f"""
            <div style="font-family:'Space Grotesk',sans-serif;background:#080D1A;color:#E2E8F0;
                        border-radius:10px;padding:14px;min-width:240px;max-width:300px;
                        border:1px solid {color}40;">
              <div style="font-size:10px;font-family:monospace;color:{color};letter-spacing:.1em;
                          text-transform:uppercase;margin-bottom:6px;">{event}</div>
              <div style="font-size:14px;font-weight:600;margin-bottom:8px;">{area[:60]}</div>
              <div style="font-size:11px;color:#94A3B8;margin-bottom:8px;">{headline[:120]}</div>
              <div style="font-size:11px;border-left:2px solid {color};padding-left:8px;
                          color:#CBD5E1;line-height:1.5;">
                {(instruction[:200]+'…') if len(instruction) > 200 else instruction or 'No specific instructions.'}
              </div>
              <div style="margin-top:10px;font-size:10px;font-family:monospace;color:#374151;">
                Severity: {sev}
              </div>
            </div>"""
            folium.Polygon(
                locations=coords,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.18,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"⚠ {event} — {area[:50]}",
            ).add_to(m)
            count += 1

    # ── TRAJECTOIRES (historique des positions) ───────────────────
    for alert_id, history in trajectories.items():
        if len(history) < 2:
            continue
        path = [(lat, lon) for lat, lon, _ in history]
        # Ligne pointillée blanche
        folium.PolyLine(
            locations=path,
            color="#FFFFFF",
            weight=2,
            opacity=0.5,
            dash_array="6 4",
            tooltip="Trajectoire de la tornade",
        ).add_to(m)
        # Points intermédiaires (positions passées)
        for lat, lon, ts in history[:-1]:
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color="#FF6B35",
                fill=True,
                fill_color="#FF6B35",
                fill_opacity=0.7,
                tooltip=f"Position à {ts} UTC",
            ).add_to(m)

    # ── MARQUEURS POSITION LIVE (centroïdes des alertes actives) ──
    for alert_id, pos in tornado_positions.items():
        if pos['event'] not in show_events:
            continue
        is_emergency = pos['event'] == "Tornado Emergency"
        color_live   = "#FF0000" if is_emergency else "#FF3B30"

        popup_html = f"""
        <div style="font-family:monospace;background:#080D1A;color:#E2E8F0;
                    padding:12px;border-radius:8px;border:1px solid {color_live};min-width:220px;">
          <div style="color:{color_live};font-size:10px;letter-spacing:.1em;margin-bottom:6px;">
            🌪️ {pos['event'].upper()} — POSITION LIVE
          </div>
          <div style="font-size:13px;font-weight:600;margin-bottom:8px;">{pos['area'][:60]}</div>
          <div style="font-size:11px;color:#94A3B8;">Sévérité : {pos['severity']}</div>
          <div style="font-size:10px;color:#4A6FA5;margin-top:6px;padding-top:6px;
                      border-top:1px solid #1A2540;">
            📍 Position estimée · centroïde du polygone NWS
          </div>
        </div>"""

        # Cercles concentriques (effet radar pulsant)
        for radius, opacity in [(28, 0.04), (18, 0.08), (10, 0.15)]:
            folium.CircleMarker(
                location=[pos['lat'], pos['lon']],
                radius=radius,
                color=color_live,
                weight=1,
                fill=True,
                fill_color=color_live,
                fill_opacity=opacity,
            ).add_to(m)

        # Marqueur principal
        folium.Marker(
            location=[pos['lat'], pos['lon']],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"🌪️ LIVE — {pos['event']} · {pos['area'][:40]}",
            icon=folium.Icon(
                color="red" if is_emergency else "orange",
                icon="bolt",
                prefix="fa",
            ),
        ).add_to(m)

    # ── TRAJECTOIRES SPC (tornades confirmées du jour) ───────────
    for group in spc_groups:
        if not group:
            continue

        # Ligne pointillée rouge reliant les points dans l'ordre chronologique
        if len(group) >= 2:
            path = [(rep['lat'], rep['lon']) for rep in group]
            folium.PolyLine(
                locations=path,
                color="#FF3B30",
                weight=2.5,
                opacity=0.8,
                dash_array="8 5",
                tooltip="Trajectoire SPC confirmée (~30min délai)",
            ).add_to(m)

        # Points pour chaque observation
        for idx, rep in enumerate(group):
            is_last = (idx == len(group) - 1)
            # Dernier point = plus grand (observation la plus récente)
            radius     = 10 if is_last else 7
            fill_op    = 0.9 if is_last else 0.7
            f_scale    = rep['f_scale'] or 'NC'
            popup_html = f"""
            <div style="font-family:monospace;background:#080D1A;color:#E2E8F0;
                        padding:12px;border-radius:8px;border:1px solid #FF3B30;min-width:210px;">
              <div style="color:#FF3B30;font-size:10px;letter-spacing:.1em;margin-bottom:6px;">
                🌪️ TORNADE CONFIRMÉE — SPC
              </div>
              <div style="font-size:13px;font-weight:600;margin-bottom:6px;">
                {rep['location']}, {rep['state']}
              </div>
              <div style="font-size:11px;color:#94A3B8;margin-bottom:4px;">
                Magnitude : <strong style="color:#FF6B6B;">{f_scale}</strong>
                &nbsp;·&nbsp; {rep['time'][:2]}:{rep['time'][2:4]} UTC
              </div>
              {'<div style="font-size:11px;color:#CBD5E1;margin-top:6px;border-top:1px solid #1A2540;padding-top:6px;">'+rep["comments"][:120]+'</div>' if rep['comments'] else ''}
              <div style="font-size:10px;color:#374151;margin-top:8px;">
                ⚠ Données SPC · délai ~10–30 min
              </div>
            </div>"""
            folium.CircleMarker(
                location=[rep['lat'], rep['lon']],
                radius=radius,
                color="#FF3B30",
                weight=2,
                fill=True,
                fill_color="#FF3B30",
                fill_opacity=fill_op,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"🌪️ {rep['location']}, {rep['state']} · {f_scale} · {rep['time'][:2]}:{rep['time'][2:4]} UTC",
            ).add_to(m)

    return m, count

# ==========================================
# 📊  SPARKLINE DATA
# ==========================================
def build_sparkline(features):
    now = datetime.now(timezone.utc)
    buckets = [0] * 24
    for f in features:
        onset = parse_time(f["properties"].get("onset"))
        if onset:
            hrs_ago = int((now - onset).total_seconds() / 3600)
            idx = 23 - min(hrs_ago, 23)
            buckets[idx] += 1
    return buckets

# ==========================================
# 📤  EXPORT HELPERS
# ==========================================
def export_csv(features):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ID","Event","Zone","Severity","Certainty","Onset","Expires","Headline"])
    for f in features:
        p = f["properties"]
        w.writerow([
            p.get("id",""), p.get("event",""), p.get("areaDesc",""),
            p.get("severity",""), p.get("certainty",""),
            p.get("onset",""), p.get("expires",""), p.get("headline",""),
        ])
    return buf.getvalue()

def export_json(features):
    simplified = []
    for f in features:
        p = f["properties"]
        simplified.append({
            "id": p.get("id",""), "event": p.get("event",""),
            "area": p.get("areaDesc",""), "severity": p.get("severity",""),
            "certainty": p.get("certainty",""), "onset": p.get("onset",""),
            "expires": p.get("expires",""), "headline": p.get("headline",""),
            "instruction": p.get("instruction",""),
        })
    return json.dumps(simplified, indent=2, ensure_ascii=False)

# ==========================================
# 🔄  SESSION STATE INIT
# ==========================================
if "last_fetch"          not in st.session_state: st.session_state.last_fetch          = time.time()
if "refresh_interval"    not in st.session_state: st.session_state.refresh_interval    = 60
if "selected_alert"      not in st.session_state: st.session_state.selected_alert      = None
if "filter_sev"          not in st.session_state: st.session_state.filter_sev          = "All"
if "show_events"         not in st.session_state: st.session_state.show_events         = set(NWS_EVENTS)
if "known_alert_ids"     not in st.session_state: st.session_state.known_alert_ids     = set()
if "email_enabled"       not in st.session_state: st.session_state.email_enabled       = True
if "emails_sent"         not in st.session_state: st.session_state.emails_sent         = 0
if "tornado_trajectories" not in st.session_state: st.session_state.tornado_trajectories = {}

# ==========================================
# 🖥️  TOPBAR
# ==========================================
now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M:%S UTC")
st.markdown(f"""
<div class="vortex-topbar">
  <div class="vortex-logo">
    <div class="vortex-logo-icon">🌪</div>
    <div>
      <div class="vortex-logo-text">VORTEX</div>
      <div class="vortex-logo-sub">SEVERE WEATHER INTELLIGENCE</div>
    </div>
  </div>
  <div class="vortex-status">
    <div class="vortex-status-dot"></div>
    NOAA / NWS LIVE &nbsp;·&nbsp; {now_utc}
  </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 📡  FETCH DATA
# ==========================================
with st.spinner(""):
    all_features = fetch_all_alerts()

# Tri par sévérité
all_features.sort(key=lambda f: SEVERITY_ORDER.get(f["properties"].get("severity","Unknown"), 4))

# Positions live des tornades + mise à jour trajectoires
tornado_positions = extract_tornado_positions(all_features)
update_trajectories(tornado_positions)
trajectories = st.session_state.tornado_trajectories

# Rapports SPC tornades du jour + regroupement en trajectoires
spc_reports  = fetch_spc_tornado_reports()
spc_groups   = group_spc_trajectories(spc_reports)

# ==========================================
# 📧  DÉTECTION NOUVELLES ALERTES + EMAIL
# ==========================================
if st.session_state.email_enabled:
    new_alerts_to_notify = []
    for f in all_features:
        props = f["properties"]
        fid   = props.get("id", "") or f.get("id", "")
        event = props.get("event", "")
        if event in EMAIL_TRIGGER_EVENTS and fid and fid not in st.session_state.known_alert_ids:
            onset_dt = parse_time(props.get("onset"))
            new_alerts_to_notify.append({
                "event":       event,
                "area":        props.get("areaDesc", "Zone inconnue"),
                "severity":    props.get("severity", "—"),
                "certainty":   props.get("certainty", "—"),
                "onset":       onset_dt.strftime("%Y-%m-%d %H:%M UTC") if onset_dt else "—",
                "instruction": props.get("instruction", "") or "Mettez-vous à l'abri immédiatement.",
            })
            st.session_state.known_alert_ids.add(fid)

    if new_alerts_to_notify:
        sent = send_alert_email(new_alerts_to_notify)
        if sent:
            st.session_state.emails_sent += len(new_alerts_to_notify)
            st.toast(f"📧 Email envoyé — {len(new_alerts_to_notify)} nouvelle(s) alerte(s) !", icon="🌪️")

# ==========================================
# 📊  COMPUTE STATS
# ==========================================
event_counts = {e: 0 for e in NWS_EVENTS}
sev_counts   = {"Extreme": 0, "Severe": 0, "Moderate": 0, "Minor": 0}
for f in all_features:
    ev  = f["properties"].get("event","")
    sev = f["properties"].get("severity","Unknown")
    if ev  in event_counts: event_counts[ev]  += 1
    if sev in sev_counts:   sev_counts[sev]   += 1

tornado_warnings    = event_counts.get("Tornado Warning", 0)
tornado_emergencies = event_counts.get("Tornado Emergency", 0)
tornado_watches     = event_counts.get("Tornado Watch", 0)
tstorm_warnings     = event_counts.get("Severe Thunderstorm Warning", 0)
total_active        = len(all_features)

# ==========================================
# 📈  METRIC CARDS
# ==========================================
st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

def metric_card(label, value, color, sub):
    st.markdown(f"""
    <div class="metric-card" style="border-top:2px solid {color};border-radius:12px;
         background:#080D1A;border:1px solid #0F1E38;padding:1rem 1.25rem;">
      <div class="metric-label">{label}</div>
      <div class="metric-value" style="color:{color};">{value}</div>
      <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

mc1, mc2, mc3, mc4, mc5 = st.columns(5)
with mc1:
    c = "#FF3B30" if tornado_warnings > 0 else "#22C55E"
    metric_card("TORNADO WARNINGS", tornado_warnings, c, "active polygons")
with mc2:
    c = "#FF3B30" if tornado_emergencies > 0 else "#4A6FA5"
    metric_card("TORNADO EMERGENCIES", tornado_emergencies, c, "highest severity")
with mc3:
    c = "#F59E0B" if tornado_watches > 0 else "#4A6FA5"
    metric_card("TORNADO WATCHES", tornado_watches, c, "counties at risk")
with mc4:
    c = "#F59E0B" if tstorm_warnings > 0 else "#4A6FA5"
    metric_card("SEVERE T-STORM WARN.", tstorm_warnings, c, "active cells")
with mc5:
    metric_card("TOTAL ACTIVE ALERTS", total_active, "#3B82F6", "all event types")

# ==========================================
# 🕒  AUTO-REFRESH BAR
# ==========================================
st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
col_refresh, col_interval, col_email = st.columns([3, 1, 1])

with col_refresh:
    elapsed   = int(time.time() - st.session_state.last_fetch)
    interval  = st.session_state.refresh_interval
    remaining = max(0, interval - elapsed)
    pct       = int((elapsed / interval) * 100) if interval > 0 else 100

    if elapsed >= interval:
        st.session_state.last_fetch = time.time()
        fetch_all_alerts.clear()
        st.rerun()

    st.markdown(f"""
    <div class="refresh-bar">
      <span class="refresh-label">NEXT SCAN IN</span>
      <div class="progress-track">
        <div class="progress-fill-bar" style="width:{pct}%"></div>
      </div>
      <span class="refresh-countdown">{remaining}s</span>
    </div>
    """, unsafe_allow_html=True)

with col_interval:
    interval_choice = st.selectbox(
        "REFRESH INTERVAL",
        options=[30, 60, 120, 300],
        index=1,
        format_func=lambda x: f"{x}s" if x < 60 else f"{x//60}min",
        label_visibility="collapsed",
    )
    if interval_choice != st.session_state.refresh_interval:
        st.session_state.refresh_interval = interval_choice
        st.session_state.last_fetch = time.time()

with col_email:
    email_on = st.toggle(
        "📧 Alertes email",
        value=st.session_state.email_enabled,
        help="Reçoit un email à alexbailly82@gmail.com dès qu'un Tornado Warning ou Tornado Emergency apparaît"
    )
    st.session_state.email_enabled = email_on
    if email_on:
        st.markdown(
            f'<div style="font-size:10px;font-family:monospace;color:#22C55E;margin-top:2px;">'
            f'✓ ACTIF · {st.session_state.emails_sent} envoyé(s)</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="font-size:10px;font-family:monospace;color:#4A6FA5;margin-top:2px;">⏸ DÉSACTIVÉ</div>',
            unsafe_allow_html=True
        )

# ==========================================
# 🗺️  MAIN CONTENT: MAP + ALERT LIST
# ==========================================
st.markdown('<div style="padding: 0.75rem 2rem 0; display:flex; flex-direction:column; gap:1rem;">', unsafe_allow_html=True)

col_map, col_list = st.columns([3, 2], gap="medium")

# ---- LEFT: MAP ----
with col_map:
    st.markdown("""
    <div class="panel" style="padding:1rem;">
      <div class="section-header">
        <span class="section-title">LIVE RADAR — THREAT POLYGONS</span>
        <span class="section-badge live">● LIVE</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    selected_events = st.multiselect(
        "VISIBLE LAYERS",
        options=NWS_EVENTS,
        default=NWS_EVENTS,
        label_visibility="collapsed",
    )
    if not selected_events:
        selected_events = NWS_EVENTS

    # Appel build_map avec les nouveaux paramètres
    radar_map, poly_count = build_map(
        all_features,
        set(selected_events),
        tornado_positions,
        trajectories,
        spc_groups,
    )

    map_result = st_folium(
        radar_map,
        width=None,
        height=480,
        returned_objects=[],
        use_container_width=True,
    )

    # Légende événements
    legend_parts = []
    for e in NWS_EVENTS:
        col_hex = EVENT_COLORS.get(e, "#6B7280")
        cnt = event_counts.get(e, 0)
        legend_parts.append(
            f'<span style="font-size:11px;font-family:monospace;padding:3px 10px;border-radius:4px;'
            f'background:rgba(255,255,255,0.03);border:1px solid #1A2540;color:#4A6FA5;">'
            f'<span style="color:{col_hex};">&#9632;</span> {e} ({cnt})</span>'
        )
    legend_html = '<div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;">' + "".join(legend_parts) + "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    # Légende des éléments live
    n_live = len(tornado_positions)
    n_spc  = sum(len(g) for g in spc_groups)
    extras = []
    if n_live > 0:
        extras.append(
            f'<span style="font-size:11px;font-family:monospace;padding:3px 10px;border-radius:4px;'
            f'background:rgba(255,59,48,0.08);border:1px solid rgba(255,59,48,0.3);color:#FF6B6B;">'
            f'⚡ {n_live} alerte(s) live — zone NWS</span>'
        )
    if n_spc > 0:
        extras.append(
            f'<span style="font-size:11px;font-family:monospace;padding:3px 10px;border-radius:4px;'
            f'background:rgba(255,59,48,0.06);border:1px solid rgba(255,59,48,0.2);color:#94A3B8;">'
            f'🌪️ {n_spc} position(s) SPC confirmée(s) · ~30min délai</span>'
        )
    if extras:
        st.markdown(
            '<div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap;">' + "".join(extras) + "</div>",
            unsafe_allow_html=True
        )

# ---- RIGHT: ALERT LOG ----
with col_list:

    # CSS animations pour les cartes
    st.markdown("""
    <style>
    @keyframes glow-red {
        0%, 100% { box-shadow: 0 0 6px rgba(255,59,48,0.3); }
        50%       { box-shadow: 0 0 18px rgba(255,59,48,0.7); }
    }
    @keyframes glow-orange {
        0%, 100% { box-shadow: 0 0 4px rgba(245,158,11,0.2); }
        50%       { box-shadow: 0 0 12px rgba(245,158,11,0.5); }
    }
    .alert-card-extreme { animation: glow-red 2s infinite; }
    .alert-card-severe  { animation: glow-orange 3s infinite; }
    </style>
    """, unsafe_allow_html=True)

    # ── Filtres sévérité ──────────────────────────────────────────
    sev_filter = st.radio(
        "Filter",
        ["All", "Extreme", "Severe", "Moderate"],
        horizontal=True,
        label_visibility="collapsed",
    )

    filtered = all_features
    if sev_filter != "All":
        filtered = [f for f in all_features if f["properties"].get("severity") == sev_filter]

    n_filtered = len(filtered)

    # ── Header ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                margin-bottom:10px;padding:0 2px;">
      <span style="font-size:11px;font-family:monospace;letter-spacing:.15em;
                   color:#4A6FA5;text-transform:uppercase;">ALERT LOG</span>
      <span style="font-size:10px;font-family:monospace;padding:3px 10px;
                   border-radius:20px;background:#0F1E38;color:#4A6FA5;
                   border:1px solid #1A2540;">{n_filtered} EVENTS</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Vide ─────────────────────────────────────────────────────
    if not filtered:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#4A6FA5;font-family:monospace;">
          <div style="font-size:32px;margin-bottom:12px;opacity:0.4;">✓</div>
          <div style="font-size:13px;">Aucune alerte active</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # On construit TOUTES les cartes en un seul bloc HTML
        # et on utilise components.html() pour éviter le sanitiseur Streamlit
        import streamlit.components.v1 as components

        cards_html = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@600;700&display=swap');
        @keyframes glow-red {
            0%,100% { box-shadow:0 0 6px rgba(255,59,48,0.3); }
            50%      { box-shadow:0 0 18px rgba(255,59,48,0.7); }
        }
        @keyframes glow-orange {
            0%,100% { box-shadow:0 0 4px rgba(245,158,11,0.2); }
            50%      { box-shadow:0 0 12px rgba(245,158,11,0.5); }
        }
        body { margin:0; padding:0; background:transparent; }
        .ac { border-radius:12px; padding:14px 16px; margin-bottom:10px; font-family:'Space Grotesk',sans-serif; }
        .ac.extreme { animation:glow-red 2s infinite; }
        .ac.severe  { animation:glow-orange 3s infinite; }
        .ac-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
        .ac-badge { font-size:10px; font-family:'JetBrains Mono',monospace; font-weight:600;
                    letter-spacing:.1em; text-transform:uppercase; padding:3px 8px; border-radius:5px; }
        .ac-ago { font-size:10px; font-family:'JetBrains Mono',monospace; color:#4A6FA5; }
        .ac-area { font-size:14px; font-weight:700; color:#F1F5F9; line-height:1.4; margin-bottom:10px; }
        .ac-tags { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
        .ac-tag { font-size:10px; font-family:'JetBrains Mono',monospace; padding:3px 9px;
                  border-radius:5px; border:1px solid; }
        .ac-time { font-size:10px; font-family:'JetBrains Mono',monospace; color:#4A6FA5; margin-bottom:8px; }
        .ac-instr { font-size:11px; color:#94A3B8; line-height:1.6;
                    padding:8px 10px 8px 12px; border-radius:0 6px 6px 0;
                    background:rgba(0,0,0,0.25); }
        </style>
        """

        for f in filtered[:20]:
            props       = f["properties"]
            event_raw   = props.get("event", "Unknown")
            area_raw    = props.get("areaDesc", "Unknown Zone")
            sev         = props.get("severity", "Unknown")
            certainty_r = props.get("certainty", "—")
            onset_raw   = props.get("onset")
            expires_raw = props.get("expires")
            onset_dt    = parse_time(onset_raw)
            expires_dt  = parse_time(expires_raw)
            time_ago    = format_time_ago(onset_dt)
            instr_raw   = props.get("instruction", "") or "Take shelter immediately."

            # Échapper tous les champs texte
            event       = html_mod.escape(event_raw)
            area        = html_mod.escape(area_raw)
            certainty   = html_mod.escape(certainty_r)
            instruction = html_mod.escape(instr_raw)
            color       = EVENT_COLORS.get(event_raw, "#6B7280")

            # Couleurs selon sévérité
            if sev == "Extreme":
                border_color = "#FF3B30"; bg_color = "rgba(255,59,48,0.06)"
                anim_class = "extreme"; badge_bg = "rgba(255,59,48,0.15)"; badge_color = "#FF6B6B"
            elif sev == "Severe":
                border_color = "#F59E0B"; bg_color = "rgba(245,158,11,0.05)"
                anim_class = "severe"; badge_bg = "rgba(245,158,11,0.15)"; badge_color = "#FBB040"
            elif sev == "Moderate":
                border_color = "#3B82F6"; bg_color = "rgba(59,130,246,0.04)"
                anim_class = ""; badge_bg = "rgba(59,130,246,0.15)"; badge_color = "#60A5FA"
            else:
                border_color = "#374151"; bg_color = "rgba(55,65,81,0.04)"
                anim_class = ""; badge_bg = "rgba(55,65,81,0.15)"; badge_color = "#94A3B8"

            # Expiration
            if expires_dt:
                now_t     = datetime.now(timezone.utc)
                mins_left = int((expires_dt - now_t).total_seconds() / 60)
                if mins_left <= 0:
                    expires_str = "Expire"; exp_color = "#374151"
                elif mins_left < 30:
                    expires_str = f"Expire {mins_left}min"; exp_color = "#F59E0B"
                else:
                    hrs  = mins_left // 60
                    mins = mins_left % 60
                    expires_str = f"Expire {f'{hrs}h ' if hrs else ''}{mins}min"
                    exp_color = "#4A6FA5"
            else:
                expires_str = "—"; exp_color = "#374151"

            onset_str = onset_dt.strftime('%Y-%m-%d %H:%M UTC') if onset_dt else "—"
            instr_short = instruction[:200] + ("…" if len(instruction) > 200 else "")

            cards_html += f"""
            <div class="ac {anim_class}" style="background:{bg_color};border:1px solid {border_color}40;border-left:4px solid {border_color};">
              <div class="ac-top">
                <span class="ac-badge" style="color:{color};background:{badge_bg};">{event}</span>
                <span class="ac-ago">{time_ago}</span>
              </div>
              <div class="ac-area">{area}</div>
              <div class="ac-tags">
                <span class="ac-tag" style="background:{badge_bg};color:{badge_color};border-color:{border_color}50;">&#9679; {sev}</span>
                <span class="ac-tag" style="background:rgba(255,255,255,0.04);color:#94A3B8;border-color:#1A2540;">{certainty}</span>
                <span class="ac-tag" style="background:rgba(255,255,255,0.04);color:{exp_color};border-color:#1A2540;">{expires_str}</span>
              </div>
              <div class="ac-time">&#128336; Emis : {onset_str}</div>
              <div class="ac-instr" style="border-left:2px solid {border_color}60;">{instr_short}</div>
            </div>
            """

        # Hauteur dynamique selon nombre d'alertes
        card_height = min(len(filtered[:20]) * 220, 900)
        components.html(cards_html, height=card_height, scrolling=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 📈  SPARKLINE TIMELINE
# ==========================================
import streamlit.components.v1 as components

buckets = build_sparkline(all_features)
max_b   = max(buckets) if max(buckets) > 0 else 1
now_h   = datetime.now(timezone.utc).hour

bars_html_parts = []
for i, b in enumerate(buckets):
    h          = (now_h - 23 + i) % 24
    height_px  = max(8, int((b / max_b) * 40))
    color      = "#FF3B30" if b >= 3 else "#F59E0B" if b >= 1 else "#1A2540"
    opacity    = "1.0" if i == 23 else "0.7"
    label      = "NOW" if i == 23 else f"{h:02d}"
    bars_html_parts.append(
        f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;" title="{h:02d}:00 UTC - {b} alert(s)">'
        f'<div style="width:100%;height:{height_px}px;background:{color};opacity:{opacity};border-radius:2px 2px 0 0;"></div>'
        f'<div style="font-size:9px;font-family:monospace;color:#374151;">{label}</div>'
        f'</div>'
    )

sparkline_html = """
<div style="background:#080D1A;border:1px solid #0F1E38;border-radius:16px;padding:1rem 1.25rem;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
    <span style="font-size:11px;font-family:monospace;letter-spacing:.15em;color:#4A6FA5;">ALERT ACTIVITY — LAST 24H</span>
    <span style="font-size:10px;font-family:monospace;padding:3px 10px;border-radius:20px;background:#0F1E38;color:#4A6FA5;border:1px solid #1A2540;">""" + str(total_active) + """ ACTIVE NOW</span>
  </div>
  <div style="display:flex;align-items:flex-end;gap:3px;height:56px;">
""" + "".join(bars_html_parts) + """
  </div>
</div>
"""
components.html(sparkline_html, height=110, scrolling=False)

# ==========================================
# 💾  EXPORT + MANUAL REFRESH
# ==========================================
st.markdown('<div style="padding: 1rem 2rem 2rem; display:flex; gap:12px; flex-wrap:wrap;">', unsafe_allow_html=True)
col_csv, col_json, col_reload, col_spacer = st.columns([1, 1, 1, 3])

with col_csv:
    st.download_button(
        "⬇ Export CSV",
        data=export_csv(all_features),
        file_name=f"vortex_alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

with col_json:
    st.download_button(
        "⬇ Export JSON",
        data=export_json(all_features),
        file_name=f"vortex_alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
    )

with col_reload:
    if st.button("↺  Force Scan"):
        fetch_all_alerts.clear()
        st.session_state.last_fetch = time.time()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⏱️  AUTO-RERUN (countdown ticker)
# ==========================================
time.sleep(1)
st.rerun()
