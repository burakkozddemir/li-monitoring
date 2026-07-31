#!/bin/bash
# li-monitoring optimizasyon/kalibrasyon yardımcısı (root gerektirir)
# Kullanım: li-battery-ctl on|off|status

set -e

BAT=/sys/class/power_supply/BAT0
CALL=/proc/acpi/call

sbmc_on() {
    echo '\\_SB.PCI0.LPCB.EC0.VPC0.SBMC 0x1' > "$CALL" 2>/dev/null || true
    cat "$CALL" 2>/dev/null
}

sbmc_off() {
    echo '\\_SB.PCI0.LPCB.EC0.VPC0.SBMC 0x0' > "$CALL" 2>/dev/null || true
    cat "$CALL" 2>/dev/null
}

status() {
    if [ ! -f "$CALL" ]; then
        echo "acpi_call modülü yok: sudo modprobe acpi_call"
        exit 1
    fi
    echo '\\_SB.PCI0.LPCB.EC0.VPC0.GBMD' > "$CALL" 2>/dev/null || true
    local r
    r=$(cat "$CALL" 2>/dev/null || echo "?")
    local bit
    bit=$(( r & 1 ))
    if [ "$bit" = "1" ]; then
        echo "konservasyon: AÇIK (şarj ~%60-80'de kesilir)"
    else
        echo "konservasyon: KAPALI (şarj %100'e kadar)"
    fi
    echo "kapasite: $(cat "$BAT/capacity")%"
    echo "durum: $(cat "$BAT/status")"
}

case "${1:-status}" in
    on) sbmc_on ;;
    off) sbmc_off ;;
    status) status ;;
    *)
        echo "Kullanım: $0 on|off|status"
        exit 1
        ;;
esac
