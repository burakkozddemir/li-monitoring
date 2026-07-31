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

Özel/GPLv3 — kullanmadan önce iletişime geçin.
