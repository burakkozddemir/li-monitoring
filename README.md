# li-monitoring

Pil sağlığı analizi ve optimizasyon aracı (GTK 3). Lenovo konservasyon modunu tek tıkla açıp kapatır, kalibrasyon rehberi sunar ve çoklu dil desteğine sahiptir (EN/TR/DE/FR/ES).

## Özellikler

- Pil sağlığı (design vs. full kapasite), döngü sayısı, sıcaklık, akım/güç/voltaj izleme
- Kapasite geçmişi grafiği (240 örnek, dakikada bir kayıt)
- ⚡ Tek tıkla konservasyon modu (Lenovo `SBMC`/`GBMD` ACPI via `acpi_call`)
- 🔄 Kalibrasyon rehberi (5 adım)
- 🎨 Koyu tema, kart tabanlı arayüz, sağlık halkası
- 🌐 Dil menüsü: English, Türkçe, Deutsch, Français, Español (varsayılan: English)

## Kurulum

### Flatpak / Flathub

```bash
flatpak install flathub com.codefein.LiMonitoring
```

Sandbox içinde konservasyon modu, `flatpak-spawn --host` üzerinden host'taki
`li-battery-ctl`'yi (sudo NOPASSWD ile) çağırır. Host'ta da kurulu olmalıdır:

```bash
sudo install -m 755 li-battery-ctl.sh /usr/local/bin/li-battery-ctl
echo 'burak ALL=(ALL) NOPASSWD: /usr/local/bin/li-battery-ctl' | sudo tee /etc/sudoers.d/li-battery
```

### Yerel derleme (flatpak-builder)

```bash
flatpak install -y flathub org.gnome.Platform//47 org.gnome.Sdk//47
flatpak-builder --repo=build/repo build/app flatpak/com.codefein.LiMonitoring.json
flatpak install --user build/repo com.codefein.LiMonitoring
```

### Sistem kurulumu (Flatpak olmadan)

```bash
# Bağımlılıklar (GNOME masaüstünde GObject/GTK hazırdır)
sudo apt install python3-gi gir1.2-gtk-3.0

# Konservasyon modu için acpi-call (opsiyonel ama önerilir)
sudo apt install acpi-call-dkms linux-headers-$(uname -r)
sudo modprobe acpi_call

# Yardımcı betik (NOPASSWD sudoers kurulumu)
sudo install -m 755 li-battery-ctl.sh /usr/local/bin/li-battery-ctl
echo 'burak ALL=(ALL) NOPASSWD: /usr/local/bin/li-battery-ctl' | sudo tee /etc/sudoers.d/li-battery

# Kısayollar
sudo ln -sf "$PWD/li-monitoring.py"      /usr/local/bin/li-monitoring
sudo ln -sf "$PWD/li-monitoring-gtk.py"  /usr/local/bin/li-monitoring-gui
```

## Flathub Yayın Akışı

1. Repoyu GitHub'da **public** yapın (`github.com/burakkozddemir/li-monitoring`).
2. Etiketli sürüm push edin (`git tag v1.6.1 && git push origin v1.6.1`) —
   GitHub Actions `.github/workflows/flatpak.yml` ile Flatpak'ı derler.
3. Flathub'a kabul için [flathub/flathub](https://github.com/flathub/flathub)
   deposuna PR açın ya da doğrudan kabul edildikten sonra repo'ya
   `FLAT_MANAGER_TOKEN` secret'ı eklenip sürümler otomatik yayınlanır.

## Kullanım

```bash
li-monitoring --watch          # terminalde canlı izleme
li-monitoring --history        # geçmiş dökümü
li-monitoring --json           # tek seferlik JSON çıktısı
li-monitoring-gui              # grafik arayüz
```

## Geliştirici

**Burak Özdemir** — [github.com/burakkozddemir](https://github.com/burakkozddemir) · [codefein.com](https://codefein.com)

## Lisans

GPL-3.0-or-later — ayrıntılar için [LICENSE](LICENSE).
