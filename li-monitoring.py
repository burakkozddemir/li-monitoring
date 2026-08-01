#!/usr/bin/env python3
import os
import sys
import time
import json
import argparse
import signal
import datetime
import statistics
from pathlib import Path

POWER_SUPPLY = Path("/sys/class/power_supply")
IS_FLATPAK = Path("/.flatpak-info").exists()


def _xdg(env, fallback):
    val = os.environ.get(env)
    return Path(val) if val else Path.home() / fallback


if IS_FLATPAK:
    DATA_DIR = _xdg("XDG_DATA_HOME", ".local/share") / "li-monitoring"
else:
    DATA_DIR = Path.home() / ".li-monitoring"
LOG_FILE = DATA_DIR / "history.jsonl"

APP_NAME = "li-monitoring"
APP_VERSION = "1.6.2"
DEVELOPER = "Burak Özdemir"
GITHUB = "https://github.com/burakkozddemir"
WEBSITE = "https://codefein.com"

C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"


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


def read_u(syspath, name):
    p = syspath / name
    if not p.is_file():
        return None
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return None


def read_str(syspath, name):
    p = syspath / name
    if not p.is_file():
        return None
    try:
        return p.read_text().strip()
    except OSError:
        return None


def find_battery():
    bats = []
    for d in sorted(POWER_SUPPLY.iterdir()):
        if read_str(d, "type") == "Battery":
            bats.append(d)
    if not bats:
        return None
    return bats[0]


def collect(bat):
    return {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "capacity": read_u(bat, "capacity"),
        "status": read_str(bat, "status"),
        "technology": read_str(bat, "technology"),
        "manufacturer": read_str(bat, "manufacturer"),
        "model": read_str(bat, "model_name"),
        "serial": read_str(bat, "serial_number"),
        "cycle_count": read_u(bat, "cycle_count"),
        "energy_now": read_u(bat, "energy_now"),
        "energy_full": read_u(bat, "energy_full"),
        "energy_full_design": read_u(bat, "energy_full_design"),
        "charge_now": read_u(bat, "charge_now"),
        "charge_full": read_u(bat, "charge_full"),
        "charge_full_design": read_u(bat, "charge_full_design"),
        "voltage_now": read_u(bat, "voltage_now"),
        "voltage_min_design": read_u(bat, "voltage_min_design"),
        "voltage_max_design": read_u(bat, "voltage_max_design"),
        "current_now": read_u(bat, "current_now"),
        "power_now": read_u(bat, "power_now"),
        "temp": read_u(bat, "temp"),
        "alarm": read_str(bat, "alarm"),
    }


def health(d):
    ef = d.get("energy_full") or 0
    efd = d.get("energy_full_design") or 0
    if efd and ef:
        return ef / efd * 100
    cf = d.get("charge_full") or 0
    cfd = d.get("charge_full_design") or 0
    if cfd and cf:
        return cf / cfd * 100
    return None


def bar(value, total=100, width=24):
    value = max(0, min(value, total))
    filled = int(round(value / total * width)) if total else 0
    return "█" * filled + "░" * (width - filled)


def health_color(h):
    if h is None:
        return C_DIM
    if h >= 80:
        return C_GREEN
    if h >= 60:
        return C_YELLOW
    return C_RED


def cap_color(c):
    if c is None:
        return C_DIM
    if c >= 80:
        return C_GREEN
    if c >= 40:
        return C_YELLOW
    return C_RED


def estimate(d):
    status = d.get("status", "")
    en = d.get("energy_now") or 0
    ef = d.get("energy_full") or 0
    pwr = d.get("power_now") or 0
    if en <= 0:
        return None
    if status == "Discharging":
        if not pwr:
            return None
        return en * 3600 / pwr
    if status == "Charging" and ef > en:
        if not pwr:
            return None
        return (ef - en) * 3600 / pwr
    return None


def fmt_duration(seconds):
    if seconds is None:
        return "hesaplanamıyor"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def battery_health_grade(h):
    if h is None:
        return "belirsiz"
    if h >= 90:
        return "Mükemmel"
    if h >= 80:
        return "İyi"
    if h >= 70:
        return "Orta"
    if h >= 50:
        return "Zayıf"
    return "Kritik"


def verbose_report(d, bat):
    print(f"\n{C_BOLD}=== {APP_NAME} v{APP_VERSION} — Lİ-ON ==={C_RESET}")
    print(f"  Analiz zamanı : {d['ts']}")
    print(f"  {C_DIM}Geliştirici: {DEVELOPER} | {GITHUB} | {WEBSITE}{C_RESET}")

    print(f"\n{C_CYAN}▸ Pil Kimliği{C_RESET}")
    print(f"  Üretici       : {d.get('manufacturer') or '?'}")
    print(f"  Model         : {d.get('model') or '?'}")
    print(f"  Seri No       : {d.get('serial') or '?'}")
    print(f"  Kimya         : {d.get('technology') or '?'}")
    print(f"  Şarj döngüsü  : {d.get('cycle_count') if d.get('cycle_count') is not None else '?'} döngü")

    h = health(d)
    print(f"\n{C_CYAN}▸ Sağlık Analizi{C_RESET}")
    if h is not None:
        print(f"  Pil sağlığı   : {bar(h)} {h:.1f}%  ({battery_health_grade(h)})")
        print(f"  Yıpranma      : {100 - h:.1f}%")
    ef = d.get("energy_full")
    efd = d.get("energy_full_design")
    if ef is not None and efd is not None:
        print(f"  Mevcut kap    : {fmt_energy(ef)}")
        print(f"  Tasarım kap   : {fmt_energy(efd)}")
        print(f"  Kap kaybı     : {fmt_energy(efd - ef)}")

    cap = d.get("capacity")
    print(f"\n{C_CYAN}▸ Şarj Durumu{C_RESET}")
    if cap is not None:
        print(f"  Doluluk       : {bar(cap)} {cap}%")
    en = d.get("energy_now")
    if en is not None:
        print(f"  Enerji        : {fmt_energy(en)}")
    print(f"  Durum         : {d.get('status') or '?'}")

    print(f"\n{C_CYAN}▸ Elektriksel Değerler{C_RESET}")
    if d.get("voltage_now") is not None:
        print(f"  Voltaj        : {fmt_voltage(d['voltage_now'])}")
    if d.get("current_now") is not None:
        print(f"  Akım          : {fmt_current(d['current_now'])}")
    if d.get("power_now") is not None:
        print(f"  Güç           : {fmt_power(d['power_now'])}")
    if d.get("temp") is not None:
        print(f"  Sıcaklık      : {d['temp'] / 10:.1f} °C")

    print(f"\n{C_CYAN}▸ Süre Tahmini{C_RESET}")
    est = estimate(d)
    if est is not None:
        label = "Şarja kalan" if d.get("status") == "Charging" else "Bitime kalan"
        print(f"  {label:12}: {fmt_duration(est)}")
    else:
        print(f"  Süre tahmini  : mevcut değil (pil dolu ya da ölçüm yok)")

    p = bat / "uevent"
    if p.is_file():
        print(f"\n{C_CYAN}▸ Çekirdek Uevent{C_RESET}")
        for line in p.read_text().strip().splitlines():
            print(f"  {line}")

    dch = d.get("charge_full") or d.get("energy_full")
    print()


def battery_status_widget(bat):
    d = collect(bat)
    cap = d.get("capacity")
    status = d.get("status", "?")
    cap_c = cap_color(cap)
    print(f"\n  {C_BOLD}PİL DURUMU{C_RESET}   {C_DIM}Ctrl+C ile çık{C_RESET}")
    print(f"  {cap_c}{bar(cap)}{C_RESET}  {cap if cap is not None else '?'}%  {C_DIM}({status}){C_RESET}")

    h = health(d)
    if h is not None:
        print(f"  Sağlık        : {health_color(h)}{h:.1f}%{C_RESET}  ({battery_health_grade(h)})")
    ef = d.get("energy_full")
    efd = d.get("energy_full_design")
    if ef is not None and efd is not None:
        print(f"  Kapasite      : {fmt_energy(ef)} / {fmt_energy(efd)}")
    if d.get("power_now") is not None:
        print(f"  Güç           : {fmt_power(d['power_now'])}")
    est = estimate(d)
    if est is not None:
        label = "Şarja kalan" if status == "Charging" else "Bitime kalan"
        print(f"  {label:12}: {fmt_duration(est)}")
    if d.get("temp") is not None:
        print(f"  Sıcaklık      : {d['temp'] / 10:.1f} °C")
    print()


def status_watch(bat, interval, times):
    try:
        n = 0
        while True:
            sys.stdout.write("\033[H\033[2J")
            sys.stdout.flush()
            battery_status_widget(bat)
            n += 1
            if times and n >= times:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print()


def load_history():
    if not LOG_FILE.is_file():
        return []
    rows = []
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def append_history(row):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(row) + "\n")


def history_report():
    rows = load_history()
    if not rows:
        print("Geçmiş verisi yok. Önce '--log' ile kayıt başlat.")
        return

    caps = [r["capacity"] for r in rows if r.get("capacity") is not None]
    caps_by_status = {"Discharging": [], "Charging": []}
    powers = []
    for r in rows:
        s = r.get("status")
        if s in caps_by_status and r.get("capacity") is not None:
            caps_by_status[s].append(r["capacity"])
        if r.get("power_now"):
            powers.append(r["power_now"])

    print(f"\n{C_BOLD}=== GEÇMİŞ ANALİZİ ({len(rows)} kayıt) ==={C_RESET}")
    if caps:
        print(f"  İlk kayıt     : {rows[0]['ts']}")
        print(f"  Son kayıt     : {rows[-1]['ts']}")
        print(f"  Doluluk (ort) : {statistics.mean(caps):.1f}%")
        print(f"  Doluluk (min) : {min(caps)}%")
        print(f"  Doluluk (max) : {max(caps)}%")
        if len(caps) > 1:
            print(f"  Sapma         : {statistics.stdev(caps):.1f}%")

    for label, key in [("Deşarj", "Discharging"), ("Şarj", "Charging")]:
        lst = caps_by_status[key]
        if lst:
            print(f"  {label} ort.     : {statistics.mean(lst):.1f}% (n={len(lst)})")

    if powers:
        print(f"  Güç (ort)     : {fmt_power(statistics.mean(powers))}")
        print(f"  Güç (tepe)    : {fmt_power(max(powers))}")

    h_vals = []
    for r in rows:
        ef = r.get("energy_full") or r.get("charge_full")
        efd = r.get("energy_full_design") or r.get("charge_full_design")
        if ef and efd:
            h_vals.append(ef / efd * 100)
    if h_vals:
        print(f"  Sağlık (ilk)  : {h_vals[0]:.1f}%")
        print(f"  Sağlık (son)  : {h_vals[-1]:.1f}%")

    print()


def service_watch(bat, interval):
    def handler(sig, frame):
        sys.exit(0)

    signal.signal(signal.SIGTERM, handler)
    while True:
        row = collect(bat)
        append_history(row)
        time.sleep(interval)


def main():
    ap = argparse.ArgumentParser(
        prog="li-monitoring",
        description="Li-poly/Li-ion pil için detaylı sağlık ve şarj analizi.",
    )
    ap.add_argument("--watch", "-w", action="store_true", help="Canlı izleme modu")
    ap.add_argument("--interval", "-i", type=float, default=5.0, help="İzleme aralığı (sn), varsayılan 5")
    ap.add_argument("--times", "-n", type=int, default=0, help="İzleme adedi, 0 = sonsuza dek")
    ap.add_argument("--log", action="store_true", help="Geçmişe kaydet (arka plan/servis için)")
    ap.add_argument("--history", action="store_true", help="Geçmiş kayıtlarının analizi")
    ap.add_argument("--json", action="store_true", help="Çıktıyı JSON olarak ver")
    ap.add_argument("--version", "-v", action="store_true", help="Sürüm ve geliştirici bilgisi")
    args = ap.parse_args()

    if args.version:
        print(f"{APP_NAME} v{APP_VERSION}")
        print(f"Geliştirici: {DEVELOPER}")
        print(f"GitHub     : {GITHUB}")
        print(f"Web        : {WEBSITE}")
        return

    bat = find_battery()
    if bat is None:
        print("Pil bulunamadı. Bu bir dizüstü bilgisayar olmalı.")
        sys.exit(1)

    if args.history:
        history_report()
        return

    if args.log:
        service_watch(bat, args.interval)
        return

    d = collect(bat)

    if args.json:
        print(json.dumps(d, indent=2))
        return

    if args.watch:
        status_watch(bat, args.interval, args.times)
        return

    verbose_report(d, bat)


if __name__ == "__main__":
    main()
