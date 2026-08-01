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
HISTORY_MAX_ROWS = 10000

APP_NAME = "li-monitoring"
APP_VERSION = "1.7.1"
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
    if abs(uw) >= 1_000_000:
        return f"{uw / 1_000_000:.2f} W"
    return f"{uw / 1_000:.0f} mW"


def fmt_voltage(uv):
    return f"{uv / 1_000_000:.3f} V"


def fmt_current(ua):
    if abs(ua) >= 1_000_000:
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
        return en * 3600 / abs(pwr)
    if status == "Charging" and ef > en:
        if not pwr:
            return None
        return (ef - en) * 3600 / abs(pwr)
    return None


def fmt_duration(seconds):
    if seconds is None:
        return "n/a"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def battery_health_grade(h):
    if h is None:
        return "unknown"
    if h >= 90:
        return "Excellent"
    if h >= 80:
        return "Good"
    if h >= 70:
        return "Fair"
    if h >= 50:
        return "Poor"
    return "Critical"


def verbose_report(d, bat):
    print(f"\n{C_BOLD}=== {APP_NAME} v{APP_VERSION} ==={C_RESET}")
    print(f"  Analyzed at   : {d['ts']}")
    print(f"  {C_DIM}Developer: {DEVELOPER} | {GITHUB} | {WEBSITE}{C_RESET}")

    print(f"\n{C_CYAN}▸ Battery Identity{C_RESET}")
    print(f"  Manufacturer  : {d.get('manufacturer') or '?'}")
    print(f"  Model         : {d.get('model') or '?'}")
    print(f"  Serial No     : {d.get('serial') or '?'}")
    print(f"  Chemistry     : {d.get('technology') or '?'}")
    print(f"  Charge cycles : {d.get('cycle_count') if d.get('cycle_count') is not None else '?'}")

    h = health(d)
    print(f"\n{C_CYAN}▸ Health Analysis{C_RESET}")
    if h is not None:
        print(f"  Battery health: {bar(h)} {h:.1f}%  ({battery_health_grade(h)})")
        print(f"  Wear level    : {100 - h:.1f}%")
    ef = d.get("energy_full")
    efd = d.get("energy_full_design")
    if ef is not None and efd is not None:
        print(f"  Current cap   : {fmt_energy(ef)}")
        print(f"  Design cap    : {fmt_energy(efd)}")
        print(f"  Capacity loss : {fmt_energy(efd - ef)}")

    cap = d.get("capacity")
    print(f"\n{C_CYAN}▸ Charge Status{C_RESET}")
    if cap is not None:
        print(f"  Charge level  : {bar(cap)} {cap}%")
    en = d.get("energy_now")
    if en is not None:
        print(f"  Energy        : {fmt_energy(en)}")
    print(f"  Status        : {d.get('status') or '?'}")

    print(f"\n{C_CYAN}▸ Electrical Values{C_RESET}")
    if d.get("voltage_now") is not None:
        print(f"  Voltage       : {fmt_voltage(d['voltage_now'])}")
    if d.get("current_now") is not None:
        print(f"  Current       : {fmt_current(d['current_now'])}")
    if d.get("power_now") is not None:
        print(f"  Power         : {fmt_power(d['power_now'])}")
    if d.get("temp") is not None:
        print(f"  Temperature   : {d['temp'] / 10:.1f} °C")

    print(f"\n{C_CYAN}▸ Time Estimates{C_RESET}")
    est = estimate(d)
    if est is not None:
        label = "Time to full  " if d.get("status") == "Charging" else "Time remaining"
        print(f"  {label}: {fmt_duration(est)}")
    else:
        print(f"  Time estimate : unavailable (battery full or no power reading)")

    p = bat / "uevent"
    if p.is_file():
        print(f"\n{C_CYAN}▸ Kernel Uevent{C_RESET}")
        for line in p.read_text().strip().splitlines():
            print(f"  {line}")

    print()


def battery_status_widget(bat):
    d = collect(bat)
    cap = d.get("capacity")
    status = d.get("status", "?")
    cap_c = cap_color(cap)
    print(f"\n  {C_BOLD}BATTERY STATUS{C_RESET}   {C_DIM}Ctrl+C to quit{C_RESET}")
    print(f"  {cap_c}{bar(cap)}{C_RESET}  {cap if cap is not None else '?'}%  {C_DIM}({status}){C_RESET}")

    h = health(d)
    if h is not None:
        print(f"  Health        : {health_color(h)}{h:.1f}%{C_RESET}  ({battery_health_grade(h)})")
    ef = d.get("energy_full")
    efd = d.get("energy_full_design")
    if ef is not None and efd is not None:
        print(f"  Capacity      : {fmt_energy(ef)} / {fmt_energy(efd)}")
    if d.get("power_now") is not None:
        print(f"  Power         : {fmt_power(d['power_now'])}")
    est = estimate(d)
    if est is not None:
        label = "Time to full" if status == "Charging" else "Time remaining"
        print(f"  {label:14}: {fmt_duration(est)}")
    if d.get("temp") is not None:
        print(f"  Temperature   : {d['temp'] / 10:.1f} °C")
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
    trim_history(HISTORY_MAX_ROWS)


def trim_history(max_rows):
    if LOG_FILE.stat().st_size < 1_500_000:
        return
    rows = load_history()
    if len(rows) <= max_rows:
        return
    with LOG_FILE.open("w") as f:
        for r in rows[-max_rows:]:
            f.write(json.dumps(r) + "\n")


def history_report():
    rows = load_history()
    if not rows:
        print("No history yet. Start logging with '--log'.")
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

    print(f"\n{C_BOLD}=== HISTORY ANALYSIS ({len(rows)} records) ==={C_RESET}")
    if caps:
        print(f"  First record  : {rows[0]['ts']}")
        print(f"  Last record   : {rows[-1]['ts']}")
        print(f"  Charge (avg)  : {statistics.mean(caps):.1f}%")
        print(f"  Charge (min)  : {min(caps)}%")
        print(f"  Charge (max)  : {max(caps)}%")
        if len(caps) > 1:
            print(f"  Std deviation : {statistics.stdev(caps):.1f}%")

    for label, key in [("Discharging", "Discharging"), ("Charging", "Charging")]:
        lst = caps_by_status[key]
        if lst:
            print(f"  {label} avg   : {statistics.mean(lst):.1f}% (n={len(lst)})")

    if powers:
        print(f"  Power (avg)   : {fmt_power(statistics.mean(powers))}")
        print(f"  Power (peak)  : {fmt_power(max(powers))}")

    h_vals = []
    for r in rows:
        ef = r.get("energy_full") or r.get("charge_full")
        efd = r.get("energy_full_design") or r.get("charge_full_design")
        if ef and efd:
            h_vals.append(ef / efd * 100)
    if h_vals:
        print(f"  Health (first): {h_vals[0]:.1f}%")
        print(f"  Health (last) : {h_vals[-1]:.1f}%")

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
        description="Detailed health and charge analysis for Li-poly/Li-ion batteries.",
    )
    ap.add_argument("--watch", "-w", action="store_true", help="live monitoring mode")
    ap.add_argument("--interval", "-i", type=float, default=5.0, help="refresh interval in seconds (default 5)")
    ap.add_argument("--times", "-n", type=int, default=0, help="number of refreshes, 0 = run forever")
    ap.add_argument("--log", action="store_true", help="log samples to history (background/service use)")
    ap.add_argument("--history", action="store_true", help="analyze the recorded history")
    ap.add_argument("--json", action="store_true", help="output a one-shot snapshot as JSON")
    ap.add_argument("--version", "-v", action="store_true", help="show version and developer info")
    args = ap.parse_args()

    if args.version:
        print(f"{APP_NAME} v{APP_VERSION}")
        print(f"Developer : {DEVELOPER}")
        print(f"GitHub    : {GITHUB}")
        print(f"Web       : {WEBSITE}")
        return

    bat = find_battery()
    if bat is None:
        print("No battery found. Run this on a laptop.")
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
