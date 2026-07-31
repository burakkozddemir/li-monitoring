#!/usr/bin/env python3
import sys
import signal
import json
import time
import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
gi.require_version("cairo", "1.0")
from gi.repository import Gtk, GLib, Gdk, cairo

POWER_SUPPLY = Path("/sys/class/power_supply")
DATA_DIR = Path.home() / ".li-monitoring"
LOG_FILE = DATA_DIR / "history.jsonl"
CONFIG_FILE = Path.home() / ".config" / "li-monitoring" / "config.json"
CTL = "/usr/local/bin/li-battery-ctl"

APP_NAME = "li-monitoring"
APP_VERSION = "1.6.0"
DEVELOPER = "Burak Özdemir"
GITHUB = "https://github.com/burakkozddemir"
WEBSITE = "https://codefein.com"

DEFAULT_LANG = "en"

STRINGS = {
    "en": {
        "lang_name": "English",
        "window_title": "Battery Analysis & Optimization",
        "file": "File",
        "quit": "Quit",
        "help": "Help",
        "about": "About",
        "language": "Language",
        "about_comments": "Battery health, optimization and calibration tool",
        "about_links": "Links",
        "about_hardware": "Hardware Support",
        "status_unknown": "Status unknown",
        "conservation_on": "Conservation ON",
        "conservation_off": "Conservation OFF",
        "conservation_on_long": "Conservation mode ON. Charging stops at ~60-80%, extending battery life.",
        "conservation_off_long": "Conservation mode OFF. Battery charges to 100%.",
        "op_failed": "Operation failed. Check sudo access.",
        "btn_optimize": "Optimize",
        "btn_calibrate": "Calibrate",
        "calibrate_title": "Battery Calibration",
        "calibrate_close": "Close",
        "calibrate_subtitle": "Calibration Guide",
        "calibrate_steps": [
            "1. Charge the battery to 100% (conservation mode must be off).",
            "2. Unplug the charger and use/discharge to 2-5%.",
            "3. Charge again before the battery fully dies.",
            "4. After reaching 100%, keep it plugged in for 2 more hours.",
            "5. This cycle recalibrates the battery capacity measurement.",
        ],
        "calibrate_note": "Note: If conservation mode is ON, turn it off first; you can re-enable it after calibration.",
        "status_charging": "Charging",
        "status_discharging": "On battery",
        "status_full": "Full",
        "status_not_charging": "Not charging",
        "status_unknown2": "Unknown",
        "health": "Health",
        "health_unknown": "Health: —",
        "cycle": "Charge cycles",
        "low_alarm": "LOW BATTERY",
        "manufacturer": "Manufacturer",
        "model": "Model",
        "serial": "Serial",
        "chemistry": "Chemistry",
        "energy": "Energy",
        "capacity": "Capacity",
        "voltage": "Voltage",
        "current": "Current",
        "power": "Power",
        "temperature": "Temperature",
        "time_to_full": "Time to full",
        "time_to_empty": "Time to empty",
        "no_estimate": "Time estimate: n/a",
        "time_estimate": "Time estimate",
        "charge_level": "Charge level",
        "history_avg": "History avg",
        "samples": "samples",
        "health_good": "Good",
        "health_fair": "Fair",
        "health_poor": "Poor",
        "health_perfect": "Excellent",
        "health_average": "Average",
        "health_weak": "Weak",
        "health_critical": "Critical",
        "health_unknown_g": "Unknown",
        "battery_not_found": "No battery found",
        "battery_not_found_msg": "This should be a laptop (BAT0/bat0 not detected).",
        "graph_gathering": "Collecting charge history…",
        "graph_capacity": "Capacity (%)",
        "dev": "Developer",
        "section_details": "Details",
        "section_history": "History",
    },
    "tr": {
        "lang_name": "Türkçe",
        "window_title": "Pil Analizi ve Optimizasyonu",
        "file": "Dosya",
        "quit": "Çıkış",
        "help": "Yardım",
        "about": "Hakkında",
        "language": "Dil",
        "about_comments": "Pil sağlığı, optimizasyon ve kalibrasyon aracı",
        "about_links": "Bağlantılar",
        "about_hardware": "Donanım Desteği",
        "status_unknown": "Durum bilinmiyor",
        "conservation_on": "Konservasyon AÇIK",
        "conservation_off": "Konservasyon KAPALI",
        "conservation_on_long": "Konservasyon modu AÇIK. Pil ~%60-80'de şarjı kesilir, pil ömrü uzar.",
        "conservation_off_long": "Konservasyon modu KAPALI. Pil %100'e kadar şarj olur.",
        "op_failed": "İşlem başarısız. sudo erişimini kontrol et.",
        "btn_optimize": "Optimize Et",
        "btn_calibrate": "Kalibre Et",
        "calibrate_title": "Pil Kalibrasyonu",
        "calibrate_close": "Kapat",
        "calibrate_subtitle": "Kalibrasyon Rehberi",
        "calibrate_steps": [
            "1. Pili %100'e kadar şarj edin (konservasyon modu kapalı olmalı).",
            "2. Şarj kablosunu çıkarıp %2-5'e kadar kullanın / deşarj edin.",
            "3. Pili tamamen kapanmadan şarj edin.",
            "4. %100'e dolunca 2 saat daha şarjda bırakın.",
            "5. Bu döngü pil kapasite ölçümünü yeniden kalibre eder.",
        ],
        "calibrate_note": "Not: Konservasyon modu açıksa önce kapatın, kalibrasyon bitince tekrar açabilirsiniz.",
        "status_charging": "Şarj oluyor",
        "status_discharging": "Pil kullanımı",
        "status_full": "Dolu",
        "status_not_charging": "Şarj etmiyor",
        "status_unknown2": "Bilinmiyor",
        "health": "Sağlık",
        "health_unknown": "Sağlık: —",
        "cycle": "Şarj döngüsü",
        "low_alarm": "DÜŞÜK ŞARJ",
        "manufacturer": "Üretici",
        "model": "Model",
        "serial": "Seri No",
        "chemistry": "Kimya",
        "energy": "Enerji",
        "capacity": "Kapasite",
        "voltage": "Voltaj",
        "current": "Akım",
        "power": "Güç",
        "temperature": "Sıcaklık",
        "time_to_full": "Şarja kalan",
        "time_to_empty": "Bitime kalan",
        "no_estimate": "Süre tahmini: yok",
        "time_estimate": "Kalan süre",
        "charge_level": "Şarj seviyesi",
        "history_avg": "Geçmiş ort",
        "samples": "örnek",
        "health_good": "İyi",
        "health_fair": "Orta",
        "health_poor": "Zayıf",
        "health_perfect": "Mükemmel",
        "health_average": "Orta",
        "health_weak": "Zayıf",
        "health_critical": "Kritik",
        "health_unknown_g": "Belirsiz",
        "battery_not_found": "Pil bulunamadı",
        "battery_not_found_msg": "Bu bir dizüstü bilgisayar olmalı (BAT0/bat0 algılanmadı).",
        "graph_gathering": "Şarj geçmişi toplanıyor…",
        "graph_capacity": "Kapasite (%)",
        "dev": "Geliştirici",
        "section_details": "Detaylar",
        "section_history": "Geçmiş",
    },
    "de": {
        "lang_name": "Deutsch",
        "window_title": "Akku-Analyse & Optimierung",
        "file": "Datei",
        "quit": "Beenden",
        "help": "Hilfe",
        "about": "Über",
        "language": "Sprache",
        "about_comments": "Akku-Gesundheit, Optimierungs- und Kalibrierungswerkzeug",
        "about_links": "Links",
        "about_hardware": "Hardware-Unterstützung",
        "status_unknown": "Status unbekannt",
        "conservation_on": "Konservierung EIN",
        "conservation_off": "Konservierung AUS",
        "conservation_on_long": "Konservierungsmodus EIN. Laden stoppt bei ~60-80%, verlängert die Akkulebensdauer.",
        "conservation_off_long": "Konservierungsmodus AUS. Akku lädt bis 100%.",
        "op_failed": "Vorgang fehlgeschlagen. Sudo-Zugriff prüfen.",
        "btn_optimize": "Optimieren",
        "btn_calibrate": "Kalibrieren",
        "calibrate_title": "Akku-Kalibrierung",
        "calibrate_close": "Schließen",
        "calibrate_subtitle": "Kalibrierungsanleitung",
        "calibrate_steps": [
            "1. Akku auf 100% laden (Konservierungsmodus muss aus sein).",
            "2. Ladegerät abziehen und auf 2-5% entladen.",
            "3. Vor vollständiger Entladung wieder laden.",
            "4. Nach 100% noch 2 Stunden angeschlossen lassen.",
            "5. Dieser Zyklus kalibriert die Kapazitätsmessung neu.",
        ],
        "calibrate_note": "Hinweis: Wenn der Konservierungsmodus aktiv ist, zuerst deaktivieren; nach der Kalibrierung wieder aktivieren.",
        "status_charging": "Lädt",
        "status_discharging": "Akku",
        "status_full": "Voll",
        "status_not_charging": "Lädt nicht",
        "status_unknown2": "Unbekannt",
        "health": "Gesundheit",
        "health_unknown": "Gesundheit: —",
        "cycle": "Ladezyklen",
        "low_alarm": "AKKU NIEDRIG",
        "manufacturer": "Hersteller",
        "model": "Modell",
        "serial": "Seriennummer",
        "chemistry": "Chemie",
        "energy": "Energie",
        "capacity": "Kapazität",
        "voltage": "Spannung",
        "current": "Strom",
        "power": "Leistung",
        "temperature": "Temperatur",
        "time_to_full": "Zeit bis voll",
        "time_to_empty": "Zeit bis leer",
        "no_estimate": "Zeitschätzung: k.A.",
        "time_estimate": "Zeitschätzung",
        "charge_level": "Ladezustand",
        "history_avg": "Verlauf Ø",
        "samples": "Proben",
        "health_good": "Gut",
        "health_fair": "Mittel",
        "health_poor": "Schwach",
        "health_perfect": "Ausgezeichnet",
        "health_average": "Mittel",
        "health_weak": "Schwach",
        "health_critical": "Kritisch",
        "health_unknown_g": "Unbekannt",
        "battery_not_found": "Kein Akku gefunden",
        "battery_not_found_msg": "Dies sollte ein Laptop sein (BAT0/bat0 nicht erkannt).",
        "graph_gathering": "Ladeverlauf wird gesammelt…",
        "graph_capacity": "Kapazität (%)",
        "dev": "Entwickler",
        "section_details": "Details",
        "section_history": "Verlauf",
    },
    "fr": {
        "lang_name": "Français",
        "window_title": "Analyse et optimisation de la batterie",
        "file": "Fichier",
        "quit": "Quitter",
        "help": "Aide",
        "about": "À propos",
        "language": "Langue",
        "about_comments": "Outil de santé, optimisation et calibrage de batterie",
        "about_links": "Liens",
        "about_hardware": "Support matériel",
        "status_unknown": "Statut inconnu",
        "conservation_on": "Conservation ACTIVÉE",
        "conservation_off": "Conservation DÉSACTIVÉE",
        "conservation_on_long": "Mode conservation ACTIVÉ. La charge s'arrête à ~60-80%, prolonge la durée de vie de la batterie.",
        "conservation_off_long": "Mode conservation DÉSACTIVÉ. La batterie se charge à 100%.",
        "op_failed": "Opération échouée. Vérifiez l'accès sudo.",
        "btn_optimize": "Optimiser",
        "btn_calibrate": "Calibrer",
        "calibrate_title": "Calibrage de la batterie",
        "calibrate_close": "Fermer",
        "calibrate_subtitle": "Guide de calibrage",
        "calibrate_steps": [
            "1. Chargez la batterie à 100% (le mode conservation doit être désactivé).",
            "2. Débranchez le chargeur et utilisez/déchargez jusqu'à 2-5%.",
            "3. Rechargez avant que la batterie ne soit complètement vide.",
            "4. Après 100%, laissez branché 2 heures de plus.",
            "5. Ce cycle recalibre la mesure de capacité.",
        ],
        "calibrate_note": "Remarque : Si le mode conservation est actif, désactivez-le d'abord ; réactivez-le après le calibrage.",
        "status_charging": "En charge",
        "status_discharging": "Sur batterie",
        "status_full": "Pleine",
        "status_not_charging": "Ne charge pas",
        "status_unknown2": "Inconnu",
        "health": "Santé",
        "health_unknown": "Santé : —",
        "cycle": "Cycles",
        "low_alarm": "BATTERIE FAIBLE",
        "manufacturer": "Fabricant",
        "model": "Modèle",
        "serial": "Série",
        "chemistry": "Chimie",
        "energy": "Énergie",
        "capacity": "Capacité",
        "voltage": "Tension",
        "current": "Courant",
        "power": "Puissance",
        "temperature": "Température",
        "time_to_full": "Temps de charge",
        "time_to_empty": "Autonomie restante",
        "no_estimate": "Estimation : n.d.",
        "time_estimate": "Estimation",
        "charge_level": "Niveau de charge",
        "history_avg": "Moy. historique",
        "samples": "échantillons",
        "health_good": "Bon",
        "health_fair": "Moyen",
        "health_poor": "Faible",
        "health_perfect": "Excellent",
        "health_average": "Moyen",
        "health_weak": "Faible",
        "health_critical": "Critique",
        "health_unknown_g": "Inconnu",
        "battery_not_found": "Aucune batterie trouvée",
        "battery_not_found_msg": "Ce devrait être un ordinateur portable (BAT0/bat0 non détecté).",
        "graph_gathering": "Collecte de l'historique de charge…",
        "graph_capacity": "Capacité (%)",
        "dev": "Développeur",
        "section_details": "Détails",
        "section_history": "Historique",
    },
    "es": {
        "lang_name": "Español",
        "window_title": "Análisis y optimización de batería",
        "file": "Archivo",
        "quit": "Salir",
        "help": "Ayuda",
        "about": "Acerca de",
        "language": "Idioma",
        "about_comments": "Herramienta de salud, optimización y calibración de batería",
        "about_links": "Enlaces",
        "about_hardware": "Soporte de hardware",
        "status_unknown": "Estado desconocido",
        "conservation_on": "Conservación ACTIVADA",
        "conservation_off": "Conservación DESACTIVADA",
        "conservation_on_long": "Modo conservación ACTIVADO. La carga se detiene al ~60-80%, prolongando la vida de la batería.",
        "conservation_off_long": "Modo conservación DESACTIVADO. La batería se carga al 100%.",
        "op_failed": "Operación fallida. Comprueba el acceso sudo.",
        "btn_optimize": "Optimizar",
        "btn_calibrate": "Calibrar",
        "calibrate_title": "Calibración de batería",
        "calibrate_close": "Cerrar",
        "calibrate_subtitle": "Guía de calibración",
        "calibrate_steps": [
            "1. Carga la batería al 100% (el modo conservación debe estar desactivado).",
            "2. Desconecta el cargador y usa/descarga hasta el 2-5%.",
            "3. Vuelve a cargar antes de que se apague.",
            "4. Tras el 100%, déjala enchufada 2 horas más.",
            "5. Este ciclo recalibra la medición de capacidad.",
        ],
        "calibrate_note": "Nota: Si el modo conservación está activo, desactívalo primero; puedes reactivarlo tras calibrar.",
        "status_charging": "Cargando",
        "status_discharging": "En batería",
        "status_full": "Llena",
        "status_not_charging": "No cargando",
        "status_unknown2": "Desconocido",
        "health": "Salud",
        "health_unknown": "Salud: —",
        "cycle": "Ciclos",
        "low_alarm": "BATERÍA BAJA",
        "manufacturer": "Fabricante",
        "model": "Modelo",
        "serial": "Serie",
        "chemistry": "Química",
        "energy": "Energía",
        "capacity": "Capacidad",
        "voltage": "Voltaje",
        "current": "Corriente",
        "power": "Potencia",
        "temperature": "Temperatura",
        "time_to_full": "Tiempo de carga",
        "time_to_empty": "Autonomía restante",
        "no_estimate": "Estimación: n/d",
        "time_estimate": "Estimación",
        "charge_level": "Nivel de carga",
        "history_avg": "Prom. histórico",
        "samples": "muestras",
        "health_good": "Bueno",
        "health_fair": "Medio",
        "health_poor": "Débil",
        "health_perfect": "Excelente",
        "health_average": "Medio",
        "health_weak": "Débil",
        "health_critical": "Crítico",
        "health_unknown_g": "Desconocido",
        "battery_not_found": "No se encontró batería",
        "battery_not_found_msg": "Esto debería ser un portátil (BAT0/bat0 no detectado).",
        "graph_gathering": "Recopilando historial de carga…",
        "graph_capacity": "Capacidad (%)",
        "dev": "Desarrollador",
        "section_details": "Detalles",
        "section_history": "Historial",
    },
}

HEALTH_GRADE_KEY = {
    90: "health_perfect",
    80: "health_good",
    70: "health_fair",
    50: "health_weak",
    0: "health_critical",
}


def health_grade_key(h):
    if h is None:
        return "health_unknown_g"
    for threshold, key in sorted(HEALTH_GRADE_KEY.items(), reverse=True):
        if h >= threshold:
            return key
    return "health_critical"


def load_config():
    try:
        with CONFIG_FILE.open() as f:
            cfg = json.load(f)
        return cfg
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(cfg):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


def resolve_lang():
    cfg = load_config()
    lang = cfg.get("lang", DEFAULT_LANG)
    if lang not in STRINGS:
        lang = DEFAULT_LANG
    return lang


class I18n:
    def __init__(self):
        self.lang = resolve_lang()
        self._tr = STRINGS.get(self.lang, STRINGS[DEFAULT_LANG])

    def set_lang(self, lang):
        if lang in STRINGS:
            self.lang = lang
            self._tr = STRINGS[lang]
            cfg = load_config()
            cfg["lang"] = lang
            save_config(cfg)

    def t(self, key):
        return self._tr.get(key, STRINGS[DEFAULT_LANG].get(key, key))

    def health_grade(self, h):
        return self.t(health_grade_key(h))

    def status_text(self, status):
        return {
            "Charging": self.t("status_charging"),
            "Discharging": self.t("status_discharging"),
            "Full": self.t("status_full"),
            "Not charging": self.t("status_not_charging"),
            "Unknown": self.t("status_unknown2"),
        }.get(status, status or "—")


i18n = I18n()


def read_u(path, name):
    p = path / name
    if not p.is_file():
        return None
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return None


def read_str(path, name):
    p = path / name
    if not p.is_file():
        return None
    try:
        return p.read_text().strip()
    except OSError:
        return None


def find_battery():
    if not POWER_SUPPLY.is_dir():
        return None
    for d in sorted(POWER_SUPPLY.iterdir()):
        if read_str(d, "type") == "Battery":
            return d
    return None


def fmt_energy(uj):
    return f"{uj / 1_000_000:.2f} Wh"


def fmt_power(uw):
    if uw >= 1_000_000:
        return f"{uw / 1_000_000:.2f} W"
    return f"{uw / 1_000:.0f} mW"


def fmt_voltage(uv):
    return f"{uv / 1_000_000:.3f} V"


def fmt_current(ua):
    if ua >= 1_000_000:
        return f"{ua / 1_000_000:.2f} A"
    return f"{ua / 1_000:.0f} mA"


def fmt_duration(seconds):
    if seconds is None:
        return "—"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def health_pct(d):
    ef = d.get("energy_full") or d.get("charge_full")
    efd = d.get("energy_full_design") or d.get("charge_full_design")
    if ef and efd:
        return ef / efd * 100
    return None


def estimate(d):
    status = d.get("status", "")
    en = d.get("energy_now") or 0
    ef = d.get("energy_full") or 0
    pwr = d.get("power_now") or 0
    if en <= 0 or not pwr:
        return None
    if status == "Discharging":
        return en * 3600 / pwr
    if status == "Charging" and ef > en:
        return (ef - en) * 3600 / pwr
    return None


def status_icon(status):
    if status == "Charging":
        return "🔌"
    if status == "Discharging":
        return "🔋"
    if status == "Full":
        return "✅"
    return "⚡"


def get_conservation():
    try:
        out = subprocess.run(
            ["sudo", "-n", CTL, "status"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        for line in out.splitlines():
            if "konservasyon:" in line:
                return "AÇIK" in line
    except Exception:
        return None
    return None


CSS = b"""
window {
    background-image: linear-gradient(to bottom, #181822, #14141b);
    color: #e6e6ec;
    font-family: "DejaVu Sans", sans-serif;
}
menubar {
    background-color: #131319;
    color: #c8c8d4;
    border-bottom: 1px solid #2b2b3a;
}
menubar > menuitem {
    color: #c8c8d4;
    padding: 4px 10px;
}
menubar > menuitem:hover {
    background-color: #26263a;
    color: #ffffff;
}
menu {
    background-color: #1c1c27;
    color: #d4d4de;
    border: 1px solid #2b2b3a;
}
menu menuitem {
    color: #d4d4de;
    padding: 5px 14px;
}
menu menuitem:hover {
    background-color: #2b2b3a;
    color: #ffffff;
}

.title {
    font-size: 24px;
    font-weight: bold;
    color: #9db8ff;
    letter-spacing: 0.5px;
    padding: 2px 0 0 0;
}
.subtitle {
    font-size: 12px;
    color: #8f8fa0;
}
.card {
    background-color: #1c1c27;
    border: 1px solid #2b2b3a;
    border-radius: 12px;
    padding: 12px;
}
.card-title {
    font-size: 12px;
    font-weight: bold;
    color: #7d7d90;
    letter-spacing: 1px;
}
.m-label {
    font-size: 11px;
    color: #8f8fa0;
}
.m-value {
    font-size: 15px;
    font-weight: bold;
    color: #d4d4de;
}
.m-green { color: #6fe3a1; }
.m-yellow { color: #fdd663; }
.m-red { color: #ff8a8a; }
.m-blue { color: #7ab8ff; }
.m-dim { color: #c6c6d4; }
.grade {
    font-size: 15px;
    font-weight: bold;
}
.status-charging { color: #6fe3a1; }
.status-discharging { color: #ff8a8a; }
.status-full { color: #9db8ff; }
.health-good { color: #6fe3a1; }
.health-fair { color: #fdd663; }
.health-poor { color: #ff8a8a; }
.graph-label { font-size: 12px; color: #8f8fa0; }
.detail {
    font-size: 13px;
    color: #c6c6d4;
    background-color: #1c1c27;
    border: 1px solid #2b2b3a;
    border-radius: 12px;
    padding: 12px;
}
.opt-btn {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    background-image: none;
    border-radius: 10px;
    padding: 9px 18px;
    border: none;
}
.btn-optimize {
    background-image: linear-gradient(to bottom, #5595d8, #2f5d8f);
    border-bottom: 2px solid #22446a;
}
.btn-optimize:hover { background-image: linear-gradient(to bottom, #63a4e8, #386a9f); }
.btn-calibrate {
    background-image: linear-gradient(to bottom, #c07a35, #8a5a2a);
    border-bottom: 2px solid #6b4520;
}
.btn-calibrate:hover { background-image: linear-gradient(to bottom, #d0883e, #9d682f); }
.state-pill {
    font-size: 12px;
    font-weight: bold;
    border-radius: 12px;
    padding: 4px 12px;
}
.pill-on { background-color: #2a7a4d; color: #dfffd0; }
.pill-off { background-color: #4a4a58; color: #d0d0da; }
"""


class DonutWidget(Gtk.DrawingArea):
    def __init__(self, size=200):
        super().__init__()
        self.set_size_request(size, size)
        self.percent = 0
        self.health = None
        self.charging = False
        self.connect("draw", self.on_draw)

    def set_percent(self, p):
        self.percent = max(0, min(100, p))
        self.queue_draw()

    def set_health(self, h):
        self.health = None if h is None else max(0, min(100, h))
        self.queue_draw()

    def set_charging(self, c):
        self.charging = bool(c)
        self.queue_draw()

    def _percent_color(self, p):
        if p <= 30:
            return (0.95, 0.4, 0.4)
        if p <= 60:
            return (0.99, 0.84, 0.39)
        return (0.44, 0.89, 0.63)

    def _health_color(self, h):
        if h >= 80:
            return (0.44, 0.89, 0.63)
        if h >= 60:
            return (0.99, 0.84, 0.39)
        return (0.95, 0.4, 0.4)

    def _bolt(self, cr, cx, cy, s):
        pts = [
            (-5, -14), (4, -14), (-1, -4), (8, -4),
            (-6, 14), (-2, 3), (-9, 3),
        ]
        cr.save()
        cr.translate(cx, cy)
        cr.scale(s / 16, s / 16)
        cr.move_to(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            cr.line_to(x, y)
        cr.close_path()
        cr.set_source_rgb(1, 0.9, 0.4)
        cr.fill()
        cr.restore()

    def on_draw(self, widget, cr):
        cr.set_source_rgb(0.11, 0.11, 0.16)
        cr.paint()

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 16
        line_w = 16

        cr.set_line_width(line_w)
        cr.set_line_cap(cairo.LineCap.ROUND)

        cr.set_source_rgb(0.25, 0.25, 0.34)
        cr.arc(cx, cy, radius, 0, 2 * 3.14159265)
        cr.stroke()

        r, g, b = self._percent_color(self.percent)
        cr.set_source_rgb(r, g, b)
        cr.arc(cx, cy, radius, -3.14159265 / 2, -3.14159265 / 2 + 2 * 3.14159265 * self.percent / 100)
        cr.stroke()

        if self.charging:
            self._bolt(cr, cx, cy - radius * 0.5, 15)

        cr.set_source_rgb(1, 1, 1)
        cr.set_font_size(40)
        cr.select_font_face("DejaVu Sans", 0, 1)
        (xb, yb, tw, th, xadv, yadv) = cr.text_extents(f"%{int(self.percent)}")
        cr.move_to(cx - tw / 2, cy - radius * 0.12 + th / 2)
        cr.show_text(f"%{int(self.percent)}")

        if self.health is not None:
            r, g, b = self._health_color(self.health)
            cr.set_source_rgb(r, g, b)
            cr.set_font_size(13)
            cr.select_font_face("DejaVu Sans", 0, 0)
            htxt = f"{self.health:.0f}% {i18n.t('health')}"
            (xb, yb, tw, th, xadv, yadv) = cr.text_extents(htxt)
            cr.move_to(cx - tw / 2, cy + radius * 0.55)
            cr.show_text(htxt)

        return False


class BatteryGraph(Gtk.DrawingArea):
    def __init__(self, width=520, height=140, max_points=240):
        super().__init__()
        self.set_size_request(width, height)
        self.samples = []
        self.max_points = max_points
        self.connect("draw", self.on_draw)

    def add_sample(self, capacity):
        self.samples.append(capacity)
        if len(self.samples) > self.max_points:
            del self.samples[: len(self.samples) - self.max_points]
        self.queue_draw()

    def on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        pad_l, pad_r, pad_t, pad_b = 36, 12, 10, 20
        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b

        cr.set_line_width(1)
        cr.set_source_rgb(0.25, 0.25, 0.32)
        for i in range(0, 101, 20):
            y = pad_t + plot_h * (1 - i / 100)
            cr.move_to(pad_l, y)
            cr.line_to(w - pad_r, y)
            cr.stroke()
            cr.set_source_rgb(0.6, 0.6, 0.7)
            cr.set_font_size(10)
            cr.move_to(2, y + 4)
            cr.show_text(f"%{i}")
            cr.set_source_rgb(0.25, 0.25, 0.32)

        cr.set_source_rgb(0.36, 0.36, 0.45)
        cr.move_to(pad_l, pad_t)
        cr.line_to(pad_l, pad_t + plot_h)
        cr.line_to(w - pad_r, pad_t + plot_h)
        cr.stroke()

        n = len(self.samples)
        if n < 2:
            cr.set_source_rgb(0.5, 0.5, 0.58)
            cr.set_font_size(12)
            cr.move_to(pad_l + 8, pad_t + 20)
            cr.show_text(i18n.t("graph_gathering"))
            return

        def point(i):
            x = pad_l + plot_w * (i / (n - 1))
            y = pad_t + plot_h * (1 - max(0, min(100, self.samples[i])) / 100)
            return x, y

        cr.set_source_rgba(0.44, 0.76, 0.98, 0.15)

        x0, y0 = point(0)
        cr.move_to(x0, y0)
        for i in range(1, n):
            x, y = point(i)
            cr.line_to(x, y)
        cr.line_to(pad_l + plot_w, pad_t + plot_h)
        cr.line_to(pad_l, pad_t + plot_h)
        cr.close_path()
        cr.fill()

        cr.set_line_width(2)
        cr.set_source_rgb(0.48, 0.78, 0.96)
        cr.move_to(x0, y0)
        for i in range(1, n):
            x, y = point(i)
            cr.line_to(x, y)
        cr.stroke()

        xl, yl = point(n - 1)
        cr.set_source_rgb(0.48, 0.78, 0.96)
        cr.arc(xl, yl, 4, 0, 2 * 3.14159265)
        cr.fill()
        cr.set_source_rgb(0.1, 0.12, 0.16)
        cr.arc(xl, yl, 2, 0, 2 * 3.14159265)
        cr.fill()

        cr.set_source_rgb(0.6, 0.6, 0.7)
        cr.set_font_size(11)
        cr.move_to(pad_l + 4, h - 6)
        cr.show_text(i18n.t("graph_capacity"))
        return False


class HBar(Gtk.DrawingArea):
    def __init__(self, width=200, height=10, color=None):
        super().__init__()
        self.set_size_request(width, height)
        self.value = 0
        self.color = color or (0.44, 0.89, 0.63)
        self.connect("draw", self.on_draw)

    def set_value(self, v, color=None):
        self.value = max(0, min(100, v))
        if color:
            self.color = color
        self.queue_draw()

    @staticmethod
    def _rrect(cr, x, y, w, h, r):
        r = min(r, w / 2, h / 2)
        cr.arc(x + r, y + r, r, 3.14159, 3.14159 * 3 / 2)
        cr.arc(x + w - r, y + r, r, 3.14159 * 3 / 2, 3.14159 * 2)
        cr.arc(x + w - r, y + h - r, r, 0, 3.14159 / 2)
        cr.arc(x + r, y + h - r, r, 3.14159 / 2, 3.14159)
        cr.close_path()

    def on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        if w <= 0 or h <= 0:
            return False

        cr.set_source_rgb(0.25, 0.25, 0.34)
        self._rrect(cr, 0, 0, w, h, h / 2)
        cr.fill()

        fw = w * self.value / 100
        if fw > h:
            cr.set_source_rgb(*self.color)
            self._rrect(cr, 0, 0, fw, h, h / 2)
            cr.fill()
        return False


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent):
        super().__init__(transient_for=parent, modal=True)
        self.set_program_name(APP_NAME)
        self.set_version(APP_VERSION)
        self.set_comments(i18n.t("about_comments"))
        self.set_copyright("© 2026 Burak Özdemir")
        self.set_authors([DEVELOPER])
        self.set_website(WEBSITE)
        self.set_website_label("codefein.com")
        self.set_logo_icon_name("battery")
        self.add_credit_section(i18n.t("about_links"), [GITHUB, WEBSITE])
        self.add_credit_section(i18n.t("about_hardware"), ["Lenovo V15-IIL (conservation mode)", "Linux acpi_call"])


class LiMonitoringWindow(Gtk.Window):
    def __init__(self, battery):
        super().__init__(title=f"{APP_NAME} — {i18n.t('window_title')}")
        self.set_default_size(720, 920)
        self.set_border_width(0)
        self.battery = battery
        self.history = self.load_history()
        self.cap_samples = [r["capacity"] for r in self.history[-240:] if r.get("capacity") is not None]
        self.logged_last = None
        self.conservation = None

        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.build_menu()
        self.build_layout()

        self.timer = GLib.timeout_add_seconds(5, self.refresh)
        self.show_all()
        self.refresh()
        self.refresh_conservation()

    def build_menu(self):
        mb = Gtk.MenuBar()

        file_item = Gtk.MenuItem(label=i18n.t("file"))
        file_menu = Gtk.Menu()
        quit_item = Gtk.MenuItem(label=i18n.t("quit"))
        quit_item.connect("activate", lambda *a: self.on_destroy(None))
        file_menu.append(quit_item)
        file_item.set_submenu(file_menu)

        lang_item = Gtk.MenuItem(label=i18n.t("language"))
        lang_menu = Gtk.Menu()
        self.lang_group = []
        for code in STRINGS:
            mi = Gtk.RadioMenuItem(label=STRINGS[code]["lang_name"], group=self.lang_group or None)
            mi.set_active(code == i18n.lang)
            mi.connect("activate", self.on_lang_selected, code)
            lang_menu.append(mi)
        lang_item.set_submenu(lang_menu)

        help_item = Gtk.MenuItem(label=i18n.t("help"))
        help_menu = Gtk.Menu()
        about_item = Gtk.MenuItem(label=i18n.t("about"))
        about_item.connect("activate", self.on_about)
        help_menu.append(about_item)
        help_item.set_submenu(help_menu)

        mb.append(file_item)
        mb.append(lang_item)
        mb.append(help_item)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(mb, False, False, 0)
        self.add(vbox)
        self.vbox = vbox

    def on_lang_selected(self, item, code):
        if not item.get_active() or code == i18n.lang:
            return
        i18n.set_lang(code)
        self.set_title(f"{APP_NAME} — {i18n.t('window_title')}")
        self.btn_optimize.set_label(f"⚡ {i18n.t('btn_optimize')}")
        self.btn_calibrate.set_label(f"🔄 {i18n.t('btn_calibrate')}")
        self.sub_label.set_text(f"v{APP_VERSION}  •  {DEVELOPER}  •  {WEBSITE}")
        self.refresh()
        self.apply_conservation_ui()

    def on_about(self, *a):
        dlg = AboutDialog(self)
        dlg.run()
        dlg.destroy()

    def build_layout(self):
        grid = Gtk.Grid(column_spacing=16, row_spacing=12)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        grid.set_margin_bottom(20)
        grid.set_margin_top(6)
        self.vbox.pack_start(grid, True, True, 0)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.get_style_context().add_class("card")
        header.set_hexpand(True)
        grid.attach(header, 0, 0, 3, 1)

        tcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        tcol.set_hexpand(True)
        title = Gtk.Label(label=APP_NAME, xalign=0)
        title.get_style_context().add_class("title")
        tcol.pack_start(title, False, False, 0)

        self.sub_label = Gtk.Label(label=f"v{APP_VERSION}  •  {DEVELOPER}  •  {WEBSITE}", xalign=0)
        self.sub_label.get_style_context().add_class("subtitle")
        tcol.pack_start(self.sub_label, False, False, 0)
        header.pack_start(tcol, True, True, 0)

        self.cons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.cons_box.set_valign(Gtk.Align.CENTER)
        header.pack_start(self.cons_box, False, False, 0)

        self.cons_pill = Gtk.Label()
        self.cons_pill.get_style_context().add_class("state-pill")
        self.cons_box.pack_start(self.cons_pill, False, False, 0)

        self.donut = DonutWidget(size=200)
        grid.attach(self.donut, 0, 1, 1, 2)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right.set_valign(Gtk.Align.CENTER)
        grid.attach(right, 1, 1, 2, 2)

        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.get_style_context().add_class("grade")
        right.pack_start(self.status_label, False, False, 0)

        self.health_label = Gtk.Label()
        self.health_label.set_halign(Gtk.Align.START)
        self.health_label.get_style_context().add_class("grade")
        right.pack_start(self.health_label, False, False, 0)

        self.cycle_label = Gtk.Label()
        self.cycle_label.set_halign(Gtk.Align.START)
        right.pack_start(self.cycle_label, False, False, 0)

        self.alarm_label = Gtk.Label()
        self.alarm_label.set_halign(Gtk.Align.START)
        self.alarm_label.get_style_context().add_class("grade")
        self.alarm_label.get_style_context().add_class("status-discharging")
        self.alarm_label.set_no_show_all(True)
        right.pack_start(self.alarm_label, False, False, 0)

        det_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        det_card.get_style_context().add_class("card")
        grid.attach(det_card, 0, 3, 3, 1)

        det_title = Gtk.Label(label=i18n.t("section_details"), xalign=0)
        det_title.get_style_context().add_class("card-title")
        det_card.pack_start(det_title, False, False, 0)

        t = i18n.t
        def metric(label):
            tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            lbl = Gtk.Label(label=label, xalign=0)
            lbl.get_style_context().add_class("m-label")
            val = Gtk.Label(label="—", xalign=0)
            val.get_style_context().add_class("m-value")
            tile.pack_start(lbl, False, False, 0)
            tile.pack_start(val, False, False, 0)
            return tile, val

        self.m_grid = Gtk.Grid(column_spacing=16, row_spacing=10)
        self.m_grid.set_halign(Gtk.Align.FILL)
        self.metrics = {}
        order = [
            ("health", t("health")),
            ("cycle", t("cycle")),
            ("temp", t("temperature")),
            ("voltage", t("voltage")),
            ("current", t("current")),
            ("power", t("power")),
            ("energy", t("energy")),
            ("capacity", t("capacity")),
            ("time", t("time_estimate")),
        ]
        for i, (key, label) in enumerate(order):
            tile, val = metric(label)
            self.metrics[key] = val
            self.m_grid.attach(tile, i % 3, i // 3, 1, 1)
        det_card.pack_start(self.m_grid, False, False, 0)

        bars = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        bars.set_halign(Gtk.Align.FILL)
        bars.set_hexpand(True)
        self.bar_health = self._bar_block(bars, t("health"))
        self.bar_charge = self._bar_block(bars, t("charge_level"))
        det_card.pack_start(bars, False, False, 0)

        self.device_label = Gtk.Label(xalign=0)
        self.device_label.get_style_context().add_class("m-label")
        self.device_label.set_line_wrap(True)
        self.device_label.set_selectable(True)
        det_card.pack_start(self.device_label, False, False, 0)

        self.history_label = Gtk.Label(xalign=0)
        self.history_label.get_style_context().add_class("subtitle")
        det_card.pack_start(self.history_label, False, False, 0)

        graph_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        graph_card.get_style_context().add_class("card")
        grid.attach(graph_card, 0, 4, 3, 1)

        graph_title = Gtk.Label(label=i18n.t("section_history"), xalign=0)
        graph_title.get_style_context().add_class("card-title")
        graph_card.pack_start(graph_title, False, False, 0)

        self.graph = BatteryGraph(width=560, height=150)
        graph_card.pack_start(self.graph, False, False, 0)

        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btns.set_halign(Gtk.Align.CENTER)
        grid.attach(btns, 0, 5, 3, 1)

        self.btn_optimize = Gtk.ToggleButton(label=f"⚡ {i18n.t('btn_optimize')}")
        self.btn_optimize.get_style_context().add_class("opt-btn")
        self.btn_optimize.get_style_context().add_class("btn-optimize")
        self.btn_optimize.connect("toggled", self.on_optimize_toggled)
        btns.pack_start(self.btn_optimize, False, False, 0)

        self.btn_calibrate = Gtk.Button(label=f"🔄 {i18n.t('btn_calibrate')}")
        self.btn_calibrate.get_style_context().add_class("opt-btn")
        self.btn_calibrate.get_style_context().add_class("btn-calibrate")
        self.btn_calibrate.connect("clicked", self.on_calibrate)
        btns.pack_start(self.btn_calibrate, False, False, 0)

    def _bar_block(self, parent, label):
        block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        block.set_hexpand(True)
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.get_style_context().add_class("m-label")
        bar = HBar(width=200, height=10)
        block.pack_start(lbl, False, False, 0)
        block.pack_start(bar, False, False, 0)
        parent.pack_start(block, True, True, 0)
        return bar

    def refresh_conservation(self):
        def work():
            self.conservation = get_conservation()
            GLib.idle_add(self.apply_conservation_ui)

        t = threading.Thread(target=work, daemon=True)
        t.start()

    def apply_conservation_ui(self):
        c = self.conservation
        if c is None:
            self.cons_pill.set_text(i18n.t("status_unknown"))
            self.cons_pill.get_style_context().add_class("pill-off")
            self.btn_optimize.set_sensitive(False)
        elif c:
            self.cons_pill.set_text(i18n.t("conservation_on"))
            self.cons_pill.get_style_context().add_class("pill-on")
            self.btn_optimize.set_active(True)
        else:
            self.cons_pill.set_text(i18n.t("conservation_off"))
            self.cons_pill.get_style_context().add_class("pill-off")
            self.btn_optimize.set_active(False)
        return False

    def run_ctl(self, arg):
        try:
            out = subprocess.run(
                ["sudo", "-n", CTL, arg],
                capture_output=True, text=True, timeout=15,
            )
            return out.returncode == 0
        except Exception:
            return False

    def on_optimize_toggled(self, btn):
        GLib.idle_add(lambda: btn.set_sensitive(False))
        target = btn.get_active()

        def work():
            if target:
                ok = self.run_ctl("on")
            else:
                ok = self.run_ctl("off")
            self.conservation = target
            GLib.idle_add(self.after_optimize, ok, target)

        threading.Thread(target=work, daemon=True).start()

    def after_optimize(self, ok, target):
        self.btn_optimize.set_sensitive(True)
        self.refresh_conservation()
        if ok:
            msg = i18n.t("conservation_on_long") if target else i18n.t("conservation_off_long")
            self.toast(msg)
        else:
            self.toast(i18n.t("op_failed"))
        return False

    def on_calibrate(self, *a):
        dlg = Gtk.Dialog(
            title=i18n.t("calibrate_title"),
            transient_for=self,
            flags=0,
        )
        dlg.set_default_size(480, 320)
        dlg.add_button(i18n.t("calibrate_close"), Gtk.ResponseType.CLOSE)

        area = dlg.get_content_area()
        area.set_margin_start(16)
        area.set_margin_end(16)
        area.set_margin_top(12)
        area.set_margin_bottom(12)

        title = Gtk.Label(label=f"🔄 {i18n.t('calibrate_subtitle')}")
        title.get_style_context().add_class("grade")
        area.pack_start(title, False, False, 8)

        for s in i18n.t("calibrate_steps"):
            lbl = Gtk.Label(label=s, xalign=0)
            lbl.set_line_wrap(True)
            lbl.set_halign(Gtk.Align.START)
            area.pack_start(lbl, False, False, 5)

        note = Gtk.Label(label=i18n.t("calibrate_note"), xalign=0)
        note.get_style_context().add_class("subtitle")
        note.set_line_wrap(True)
        note.set_halign(Gtk.Align.START)
        area.pack_start(note, False, False, 10)

        dlg.show_all()
        dlg.run()
        dlg.destroy()

    def toast(self, msg):
        self.set_title(f"{APP_NAME} — {msg}")
        GLib.timeout_add(4000, lambda: self.set_title(f"{APP_NAME} — {i18n.t('window_title')}"))
        return False

    def set_metric(self, key, text, cls=None):
        val = self.metrics.get(key)
        if val is None:
            return
        ctx = val.get_style_context()
        for c in ("m-green", "m-yellow", "m-red", "m-blue", "m-dim"):
            ctx.remove_class(c)
        ctx.add_class(cls or "m-dim")
        val.set_text(text)

    def refresh(self):
        d = {}
        for name in (
            "capacity", "status", "technology", "manufacturer", "model", "serial",
            "cycle_count", "energy_now", "energy_full", "energy_full_design",
            "charge_now", "charge_full", "charge_full_design",
            "voltage_now", "current_now", "power_now", "temp",
        ):
            if name in ("status", "technology", "manufacturer", "model", "serial"):
                d[name] = read_str(self.battery, name)
            else:
                d[name] = read_u(self.battery, name)

        cap = d.get("capacity")
        status = d.get("status", "")

        if cap is not None:
            self.donut.set_percent(cap)
            self.graph.add_sample(cap)
        self.donut.set_charging(status == "Charging")

        self.status_label.set_text(f"{status_icon(status)} {i18n.status_text(status)}")

        ctx = self.status_label.get_style_context()
        for c in ("status-charging", "status-discharging", "status-full"):
            ctx.remove_class(c)
        if status == "Charging":
            ctx.add_class("status-charging")
        elif status == "Discharging":
            ctx.add_class("status-discharging")
        elif status == "Full":
            ctx.add_class("status-full")

        h = health_pct(d)
        if h is not None:
            hctx = self.health_label.get_style_context()
            for c in ("health-good", "health-fair", "health-poor"):
                hctx.remove_class(c)
            hctx.add_class(
                "health-good" if h >= 80 else "health-fair" if h >= 60 else "health-poor"
            )
            self.health_label.set_text(f"🧪 {i18n.t('health')}: {h:.1f}%  ({i18n.health_grade(h)})")
        else:
            self.health_label.set_text(i18n.t("health_unknown"))
        self.donut.set_health(h)

        cc = d.get("cycle_count")
        self.cycle_label.set_text(f"🔁 {i18n.t('cycle')}: {cc if cc is not None else '—'}")

        if cap is not None and cap <= 20:
            self.alarm_label.set_text(f"⚠ {i18n.t('low_alarm')} %{cap}")
            self.alarm_label.show()
        else:
            self.alarm_label.hide()

        t = i18n.t
        if h is not None:
            self.set_metric("health", f"{h:.1f}%",
                            "m-green" if h >= 80 else "m-yellow" if h >= 60 else "m-red")
        else:
            self.set_metric("health", "—")

        self.set_metric("cycle", str(cc) if cc is not None else "—", "m-blue" if cc is not None else None)

        tp = d.get("temp")
        if tp is not None:
            c = tp / 10.0
            self.set_metric("temp", f"{c:.1f} °C",
                            "m-green" if c < 55 else "m-yellow" if c < 65 else "m-red")
        else:
            self.set_metric("temp", "—")

        if d.get("voltage_now") is not None:
            self.set_metric("voltage", fmt_voltage(d["voltage_now"]), "m-blue")
        else:
            self.set_metric("voltage", "—")

        if d.get("current_now") is not None:
            self.set_metric("current", fmt_current(d["current_now"]),
                            "m-green" if status == "Charging" else "m-red")
        else:
            self.set_metric("current", "—")

        if d.get("power_now") is not None:
            self.set_metric("power", fmt_power(d["power_now"]),
                            "m-green" if status == "Charging" else "m-red")
        else:
            self.set_metric("power", "—")

        if d.get("energy_now") is not None:
            self.set_metric("energy", fmt_energy(d["energy_now"]))
        else:
            self.set_metric("energy", "—")

        if d.get("energy_full") is not None and d.get("energy_full_design") is not None:
            self.set_metric("capacity",
                            f"{fmt_energy(d['energy_full'])} / {fmt_energy(d['energy_full_design'])}")
        else:
            self.set_metric("capacity", "—")

        est = estimate(d)
        if est is not None:
            self.set_metric("time", fmt_duration(est), "m-blue")
        else:
            self.set_metric("time", "—")

        dev = []
        if d.get("manufacturer"):
            dev.append(d["manufacturer"])
        if d.get("model"):
            dev.append(d["model"])
        if d.get("technology"):
            dev.append(d["technology"])
        if d.get("serial"):
            dev.append(f"SN: {d['serial']}")
        self.device_label.set_text("  •  ".join(dev) if dev else "—")

        if h is not None:
            self.bar_health.set_value(h, (0.44, 0.89, 0.63) if h >= 80
                                      else (0.99, 0.84, 0.39) if h >= 60 else (0.95, 0.4, 0.4))
        else:
            self.bar_health.set_value(0, (0.25, 0.25, 0.34))
        if cap is not None:
            self.bar_charge.set_value(cap, (0.44, 0.89, 0.63) if cap >= 60
                                      else (0.99, 0.84, 0.39) if cap >= 30 else (0.95, 0.4, 0.4))
        else:
            self.bar_charge.set_value(0, (0.25, 0.25, 0.34))

        if self.cap_samples:
            self.history_label.set_text(
                f"📈 {t('history_avg')}: %{sum(self.cap_samples) / len(self.cap_samples):.1f} "
                f"({len(self.cap_samples)} {t('samples')})")
        else:
            self.history_label.set_text("")

        now = time.time()
        if self.logged_last is None or now - self.logged_last >= 60:
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                row = dict(d)
                row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                with LOG_FILE.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                self.logged_last = now
                if cap is not None:
                    self.cap_samples.append(cap)
                    if len(self.cap_samples) > 240:
                        del self.cap_samples[:-240]
            except OSError:
                pass

        return True

    def load_history(self):
        if not LOG_FILE.is_file():
            return []
        rows = []
        try:
            with LOG_FILE.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return []
        return rows

    def on_destroy(self, widget):
        if self.timer:
            GLib.source_remove(self.timer)
        Gtk.main_quit()


def main():
    battery = find_battery()
    if battery is None:
        md = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=i18n.t("battery_not_found"),
        )
        md.format_secondary_text(i18n.t("battery_not_found_msg"))
        md.run()
        md.destroy()
        return 1

    win = LiMonitoringWindow(battery)
    win.connect("destroy", win.on_destroy)
    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(main())
