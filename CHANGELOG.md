# Changelog

All notable changes to li-monitoring are documented in this file.

## [1.7.1] - 2026-08-01

### Changed
- Conservation mode is now a proper on/off switch (`Gtk.Switch`) in the GUI
  instead of a toggle button, with a clear checked/unchecked style.

## [1.7.0] - 2026-08-01

### Added
- Automated unit tests for core logic, history handling and the CLI
  (`tests/`, stdlib `unittest`).
- CI workflow that runs syntax checks and the test suite on every push/PR
  (`.github/workflows/ci.yml`).
- History log is now capped at 10 000 records (no unbounded file growth).
- CLI output is now fully in English.

### Fixed
- Time estimates were negative while discharging (negative `power_now`).
- Power/current formatting showed the wrong unit for negative values.
- The GUI no longer aborts its refresh cycle on transient read errors.
- Installer replaces an existing install instead of failing with
  "already installed".

## [1.6.2] - 2026-08-01

### Changed
- XDG-compliant data paths (config and history persist inside the Flatpak
  sandbox without extra filesystem permissions).
- GNOME runtime updated to 50 (47 was end-of-life).
- Flathub linter is clean (0 errors).
- GitHub Releases now build and publish the bundle automatically from CI.

## [1.6.1] - 2026-08-01

### Added
- Flatpak packaging support.

## [1.6.0] - 2026-08-01

### Changed
- Redesigned details section: metric grid, colored values and health/charge
  progress bars.

## [1.5.1] - 2026-08-01

### Changed
- Single-ring donut and dark-themed menus.

## [1.5.0] - 2026-08-01

### Changed
- Modern dark design refresh: cards, gradients, donut health ring, filled
  chart.
