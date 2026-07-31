# ⚡ li-monitoring

**A GTK battery health analyzer and optimizer for Linux laptops.**

li-monitoring turns raw battery telemetry from your laptop into a clear picture:
real-time capacity, charge cycles, temperature, voltage, current and power draw —
plus a one-click **conservation mode** toggle for Lenovo laptops and a guided
**calibration** routine to keep your battery's capacity measurement accurate.

![Main window](data/screenshots/main.png)

## ✨ Features

- 🧪 **Battery health analysis** — design vs. full capacity, wear level and grade
  (Excellent / Good / Fair / Poor / Critical)
- 📈 **Live charge history graph** — up to 240 samples, logged every minute
- 🍩 **Donut gauge** — charge percentage with a charging indicator, health ring
  and color-coded status
- ⚡ **One-click conservation mode** (Lenovo) — stops charging around 60–80% to
  extend battery lifetime, via the ACPI `SBMC`/`GBMD` methods (`acpi_call`)
- 🔄 **Calibration guide** — step-by-step 5-step procedure to recalibrate the
  capacity gauge
- 🧊 **Thermal & electrical telemetry** — temperature, voltage, current, power,
  energy, time-to-full / time-to-empty estimates
- 🗂️ **Rich detail panel** — a color-coded metric grid with health and charge
  progress bars
- 🌐 **5 languages** — English, Türkçe, Deutsch, Français, Español (switchable at
  runtime)
- 🎨 **Modern dark theme** — card-based layout, gradients and crisp typography
- 📊 **CLI companion** — live monitoring, history and one-shot JSON output

### Screenshots

| Calibration guide | About |
|---|---|
| ![Calibration](data/screenshots/calibration.png) | ![About](data/screenshots/about.png) |

## 🚀 Installation

### Flatpak / Flathub (recommended)

```bash
flatpak install flathub com.codefein.LiMonitoring
```

Inside the sandbox, conservation mode is handled with `flatpak-spawn --host`,
which invokes `li-battery-ctl` on the host. Make sure it is installed there too:

```bash
sudo install -m 755 li-battery-ctl.sh /usr/local/bin/li-battery-ctl
echo 'burak ALL=(ALL) NOPASSWD: /usr/local/bin/li-battery-ctl' | sudo tee /etc/sudoers.d/li-battery
```

### System-wide (without Flatpak)

```bash
# Dependencies (already present on GNOME desktops)
sudo apt install python3-gi gir1.2-gtk-3.0

# acpi-call for Lenovo conservation mode (optional but recommended)
sudo apt install acpi-call-dkms linux-headers-$(uname -r)
sudo modprobe acpi_call

# Helper script + passwordless sudo rule
sudo install -m 755 li-battery-ctl.sh /usr/local/bin/li-battery-ctl
echo 'burak ALL=(ALL) NOPASSWD: /usr/local/bin/li-battery-ctl' | sudo tee /etc/sudoers.d/li-battery

# CLI + GUI entry points
sudo ln -sf "$PWD/li-monitoring.py"      /usr/local/bin/li-monitoring
sudo ln -sf "$PWD/li-monitoring-gtk.py"  /usr/local/bin/li-monitoring-gui
```

> **Note:** Replace `burak` in the sudoers rule with your own username.
> Conservation mode is only available on hardware that exposes the Lenovo
> `SBMC`/`GBMD` ACPI methods — the Optimize button disables itself gracefully
> otherwise.

## 🖥️ Usage

Launch the graphical interface:

```bash
li-monitoring-gui
```

The terminal CLI:

```bash
li-monitoring --watch          # live monitoring in the terminal
li-monitoring --history        # dump the charge history log
li-monitoring --json           # one-shot battery snapshot as JSON
li-monitoring --version        # version and developer info
```

### Interpreting battery health

| Grade | Remaining capacity | Meaning |
|---|---|---|
| 🟢 Excellent | ≥ 95% | Like new |
| 🟢 Good | ≥ 80% | Slight wear, no action needed |
| 🟡 Fair | ≥ 60% | Noticeable wear; consider conservation mode |
| 🟠 Poor | ≥ 40% | Significant degradation |
| 🔴 Critical | < 40% | Replace the battery soon |

The **Optimize** button toggles Lenovo conservation mode: with it on, charging
stops around 60–80%, which dramatically reduces cell wear for people who keep
their laptop plugged in most of the time.

## 🔧 Development

### Local Flatpak build

```bash
flatpak install -y flathub org.gnome.Platform//47 org.gnome.Sdk//47
flatpak-builder --repo=build/repo build/app flatpak/com.codefein.LiMonitoring.json
flatpak install --user build/repo com.codefein.LiMonitoring
```

### Repository layout

```
li-monitoring/
├── li-monitoring.py              # CLI application
├── li-monitoring-gtk.py          # GTK 3 GUI
├── li-battery-ctl.sh             # conservation mode helper (host side)
├── flatpak/
│   ├── com.codefein.LiMonitoring.json      # Flatpak manifest
│   ├── com.codefein.LiMonitoring.desktop
│   └── com.codefein.LiMonitoring.metainfo.xml
├── data/
│   ├── com.codefein.LiMonitoring.svg       # application icon
│   └── screenshots/                         # README screenshots
└── .github/workflows/flatpak.yml           # Flathub build pipeline
```

### Flathub release flow

1. Tag a release (`git tag v1.6.1 && git push origin v1.6.1`).
2. GitHub Actions builds the Flatpak bundle automatically
   (`.github/workflows/flatpak.yml`).
3. Once the app is accepted on Flathub, add the `FLAT_MANAGER_TOKEN` secret to
   the repository and releases publish automatically.

## 📜 License

GPL-3.0-or-later — see [LICENSE](LICENSE).

---

**Developer:** Burak Özdemir · [github.com/burakkozddemir](https://github.com/burakkozddemir) · [codefein.com](https://codefein.com)
