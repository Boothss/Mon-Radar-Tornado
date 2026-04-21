"""
VORTEX — Script de surveillance autonome
Tourne toutes les 5 minutes via GitHub Actions.
Envoie un email si un Tornado Warning ou Tornado Emergency apparaît.
"""

import requests
import smtplib
import json
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==========================================
# ⚙️  CONFIG (via secrets GitHub)
# ==========================================
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER",   "alexbailly82@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD",  "")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER",  "alexbailly82@gmail.com")

# Alertes qui déclenchent un email
TRIGGER_EVENTS = [
    "Tornado Warning",
    "Tornado Emergency",
    "Tornado Watch",          # retirez cette ligne si trop de notifs
    "Severe Thunderstorm Warning",  # idem
]

# Fichier qui mémorise les alertes déjà notifiées
SEEN_FILE = "seen_alerts.json"

# ==========================================
# 🧠  FONCTIONS
# ==========================================
def load_seen():
    """Charge les IDs d'alertes déjà envoyées."""
    try:
        with open(SEEN_FILE, "r") as f:
            data = json.load(f)
            # Garde seulement les 500 derniers pour ne pas grossir indéfiniment
            return set(data[-500:])
    except Exception:
        return set()

def save_seen(seen_ids):
    """Sauvegarde les IDs d'alertes traitées."""
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen_ids)[-500:], f)
    except Exception:
        pass

def fetch_alerts():
    """Récupère toutes les alertes actives depuis la NOAA."""
    all_features = []
    headers = {"User-Agent": "VORTEX-Monitor/2.0 (alexbailly82@gmail.com)"}
    for event in TRIGGER_EVENTS:
        try:
            url = f"https://api.weather.gov/alerts/active?event={requests.utils.quote(event)}"
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            all_features.extend(r.json().get("features", []))
        except Exception as e:
            print(f"[WARN] Erreur fetch '{event}': {e}")
    return all_features

def build_email(new_alerts):
    """Construit l'email HTML + texte plain."""
    msg = MIMEMultipart("alternative")

    count = len(new_alerts)
    top_event = new_alerts[0]["event"]
    subject = f"🌪️ VORTEX — {count} alerte(s) : {top_event}"
    if any(a["event"] == "Tornado Emergency" for a in new_alerts):
        subject = f"🚨 TORNADO EMERGENCY — ACTION IMMÉDIATE REQUISE"

    msg["Subject"] = subject
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER

    # ── TEXTE PLAIN ──
    plain_lines = [
        "VORTEX · Severe Weather Intelligence",
        "=" * 50,
        f"  {count} NOUVELLE(S) ALERTE(S) DÉTECTÉE(S)",
        "=" * 50,
    ]
    for a in new_alerts:
        plain_lines += [
            "",
            f"  TYPE      : {a['event']}",
            f"  ZONE      : {a['area']}",
            f"  SÉVÉRITÉ  : {a['severity']}",
            f"  CERTITUDE : {a['certainty']}",
            f"  HEURE UTC : {a['onset']}",
            f"  EXPIRES   : {a['expires']}",
            "",
            f"  INSTRUCTIONS :",
            f"  {a['instruction'][:400]}",
            "",
            "  " + "-" * 46,
        ]
    plain_lines += [
        "",
        f"  Source : NOAA / National Weather Service (USA)",
        f"  Heure du scan : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    ]

    # ── HTML ──
    alert_cards = ""
    for a in new_alerts:
        if a["event"] == "Tornado Emergency":
            accent = "#FF0000"
            bg_accent = "rgba(255,0,0,0.08)"
        elif a["event"] == "Tornado Warning":
            accent = "#FF3B30"
            bg_accent = "rgba(255,59,48,0.08)"
        elif a["event"] == "Tornado Watch":
            accent = "#F59E0B"
            bg_accent = "rgba(245,158,11,0.08)"
        else:
            accent = "#3B82F6"
            bg_accent = "rgba(59,130,246,0.08)"

        expires_str = a["expires"] if a["expires"] != "—" else "Non précisé"

        alert_cards += f"""
        <div style="background:{bg_accent};border:1px solid {accent}40;border-left:4px solid {accent};
                    border-radius:10px;padding:20px 24px;margin-bottom:20px;">

          <div style="font-size:10px;font-family:monospace;color:{accent};
                      letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px;">
            ● {a['event']}
          </div>

          <div style="font-size:20px;font-weight:700;color:#FFFFFF;margin-bottom:16px;
                      line-height:1.3;">
            {a['area']}
          </div>

          <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
            <tr>
              <td style="padding:6px 12px 6px 0;font-size:12px;color:#64748B;
                         font-family:monospace;white-space:nowrap;vertical-align:top;">SÉVÉRITÉ</td>
              <td style="padding:6px 0;font-size:13px;color:#E2E8F0;font-weight:600;">{a['severity']}</td>
            </tr>
            <tr>
              <td style="padding:6px 12px 6px 0;font-size:12px;color:#64748B;
                         font-family:monospace;white-space:nowrap;vertical-align:top;">CERTITUDE</td>
              <td style="padding:6px 0;font-size:13px;color:#E2E8F0;">{a['certainty']}</td>
            </tr>
            <tr>
              <td style="padding:6px 12px 6px 0;font-size:12px;color:#64748B;
                         font-family:monospace;white-space:nowrap;vertical-align:top;">ÉMISE</td>
              <td style="padding:6px 0;font-size:13px;color:#E2E8F0;font-family:monospace;">{a['onset']}</td>
            </tr>
            <tr>
              <td style="padding:6px 12px 6px 0;font-size:12px;color:#64748B;
                         font-family:monospace;white-space:nowrap;vertical-align:top;">EXPIRE</td>
              <td style="padding:6px 0;font-size:13px;color:#E2E8F0;font-family:monospace;">{expires_str}</td>
            </tr>
          </table>

          <div style="background:#050810;border-radius:8px;padding:14px 16px;">
            <div style="font-size:10px;font-family:monospace;color:#4A6FA5;
                        letter-spacing:.1em;margin-bottom:8px;">INSTRUCTIONS OFFICIELLES</div>
            <div style="font-size:13px;color:#CBD5E1;line-height:1.7;">
              {a['instruction'][:500]}{'…' if len(a['instruction']) > 500 else ''}
            </div>
          </div>
        </div>"""

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html_body = f"""
    <html>
    <body style="margin:0;padding:0;background:#050810;">
      <div style="max-width:620px;margin:0 auto;padding:32px 24px;font-family:'Segoe UI',Arial,sans-serif;">

        <!-- HEADER -->
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:28px;
                    padding-bottom:20px;border-bottom:1px solid #0F1E38;">
          <div style="background:linear-gradient(135deg,#FF3B30,#FF6B35);border-radius:12px;
                      width:48px;height:48px;display:flex;align-items:center;
                      justify-content:center;font-size:24px;flex-shrink:0;">🌪</div>
          <div>
            <div style="color:#FFFFFF;font-size:20px;font-weight:700;letter-spacing:.15em;">VORTEX</div>
            <div style="color:#4A6FA5;font-size:10px;letter-spacing:.1em;margin-top:2px;">
              SEVERE WEATHER INTELLIGENCE · NOAA / NWS
            </div>
          </div>
        </div>

        <!-- ALERTE BANNER -->
        <div style="background:rgba(255,59,48,0.08);border:1px solid rgba(255,59,48,0.3);
                    border-radius:10px;padding:14px 20px;margin-bottom:24px;
                    display:flex;align-items:center;gap:12px;">
          <div style="width:10px;height:10px;border-radius:50%;background:#FF3B30;flex-shrink:0;"></div>
          <div style="font-size:13px;font-family:monospace;color:#FF6B6B;letter-spacing:.08em;">
            {count} NOUVELLE(S) ALERTE(S) DÉTECTÉE(S) · {now_str}
          </div>
        </div>

        <!-- ALERT CARDS -->
        {alert_cards}

        <!-- FOOTER -->
        <div style="margin-top:28px;padding-top:20px;border-top:1px solid #0F1E38;
                    font-size:11px;color:#374151;font-family:monospace;line-height:1.8;">
          <div>Source : NOAA · National Weather Service (USA)</div>
          <div>Scan automatique toutes les 5 minutes via GitHub Actions</div>
          <div style="margin-top:8px;color:#1E3A5F;">
            Pour désactiver ces notifications, retirez votre email du fichier monitor.py
          </div>
        </div>

      </div>
    </body>
    </html>"""

    msg.attach(MIMEText("\n".join(plain_lines), "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg

def send_email(msg):
    """Envoie l'email via Gmail SMTP."""
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"[OK] Email envoyé à {EMAIL_RECEIVER}")
        return True
    except Exception as e:
        print(f"[ERROR] Échec envoi email : {e}")
        return False

# ==========================================
# 🚀  MAIN
# ==========================================
if __name__ == "__main__":
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[VORTEX] Scan démarré · {now}")

    # Chargement des alertes déjà connues
    seen_ids = load_seen()
    print(f"[INFO] {len(seen_ids)} alertes déjà connues en mémoire")

    # Récupération des alertes actives
    features = fetch_alerts()
    print(f"[INFO] {len(features)} alertes actives récupérées depuis NOAA")

    # Détection des nouvelles alertes
    new_alerts = []
    new_ids    = set()

    for f in features:
        props = f["properties"]
        fid   = props.get("id", "") or f.get("id", "")
        event = props.get("event", "")

        if not fid or fid in seen_ids:
            continue  # déjà notifiée

        # Parsing de l'heure
        def parse_ts(ts):
            if not ts:
                return "—"
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                return ts

        instruction = props.get("instruction", "") or "Mettez-vous à l'abri immédiatement."

        new_alerts.append({
            "event":       event,
            "area":        props.get("areaDesc", "Zone inconnue"),
            "severity":    props.get("severity", "—"),
            "certainty":   props.get("certainty", "—"),
            "onset":       parse_ts(props.get("onset")),
            "expires":     parse_ts(props.get("expires")),
            "instruction": instruction,
        })
        new_ids.add(fid)

    print(f"[INFO] {len(new_alerts)} nouvelle(s) alerte(s) à notifier")

    # Envoi email si nouvelles alertes
    if new_alerts:
        if not EMAIL_PASSWORD:
            print("[ERROR] EMAIL_PASSWORD non défini dans les secrets GitHub")
        else:
            msg = build_email(new_alerts)
            sent = send_email(msg)
            if sent:
                # Mise à jour de la mémoire
                seen_ids.update(new_ids)
                save_seen(seen_ids)
    else:
        print("[OK] Aucune nouvelle alerte — pas d'email envoyé")

    print("[VORTEX] Scan terminé")
