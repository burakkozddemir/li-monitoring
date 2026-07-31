#!/usr/bin/env bash
#
# li-monitoring installer
# Downloads the Flatpak bundle from GitHub Releases and installs it.
#
# Usage:
#   ./install.sh                 install from latest GitHub release (user-wide)
#   ./install.sh --system        install system-wide (requires sudo)
#   ./install.sh --file FILE     install from a local .flatpak file
#   ./install.sh --remove        uninstall the app
#   ./install.sh --help          show this help
#
set -euo pipefail

APP_ID="com.codefein.LiMonitoring"
REPO="burakkozddemir/li-monitoring"
BUNDLE_URL="https://github.com/${REPO}/releases/latest/download/li-monitoring.flatpak"

usage() {
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

need_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "error: '$1' is required but not installed." >&2
        exit 1
    fi
}

install_from_file() {
    local file="$1"
    need_cmd flatpak
    echo "Installing $APP_ID from $file ..."
    flatpak install --user --assumeyes "$file"
    echo ""
    echo "Done. Run it with:  flatpak run $APP_ID"
}

do_install() {
    need_cmd curl
    need_cmd flatpak

    local tmp
    tmp=$(mktemp --suffix=.flatpak)
    trap 'rm -f "$tmp"' EXIT

    echo "Downloading latest release from GitHub ..."
    curl -fsSL "$BUNDLE_URL" -o "$tmp"
    install_from_file "$tmp"
}

do_remove() {
    need_cmd flatpak
    echo "Removing $APP_ID ..."
    flatpak uninstall --assumeyes "$APP_ID"
    echo "Done."
}

case "${1:-}" in
    --system)
        echo "System-wide install requires sudo; installing into the system repo."
        need_cmd curl
        need_cmd flatpak
        local tmp
        tmp=$(mktemp --suffix=.flatpak)
        trap 'rm -f "$tmp"' EXIT
        curl -fsSL "$BUNDLE_URL" -o "$tmp"
        sudo flatpak install --system --assumeyes "$tmp"
        echo "Done. Run it with:  flatpak run $APP_ID"
        ;;
    --file)
        [ -n "${2:-}" ] || { echo "error: --file requires a path"; usage; }
        install_from_file "$2"
        ;;
    --remove)
        do_remove
        ;;
    --help|-h)
        usage
        ;;
    "")
        do_install
        ;;
    *)
        echo "error: unknown option '$1'" >&2
        usage
        ;;
esac
