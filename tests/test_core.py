import json
import sys
import tempfile
import unittest
from pathlib import Path

import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lim = load_module(ROOT / "li-monitoring.py", "li_monitoring")


def make_fake_battery(root):
    b = Path(root) / "BAT0"
    b.mkdir(parents=True)
    files = {
        "type": "Battery",
        "capacity": "75",
        "status": "Discharging",
        "technology": "Li-poly",
        "manufacturer": "LENOVO",
        "model_name": "L19M4PD1",
        "serial_number": "1234",
        "cycle_count": "120",
        "energy_now": "40000000",
        "energy_full": "55000000",
        "energy_full_design": "60000000",
        "charge_now": "4400000",
        "charge_full": "6000000",
        "charge_full_design": "6500000",
        "voltage_now": "11560000",
        "current_now": "-1234000",
        "power_now": "-13500000",
        "temp": "312",
        "uevent": "POWER_SUPPLY_NAME=BAT0",
    }
    for name, val in files.items():
        (b / name).write_text(val + "\n")
    return b


class HealthTests(unittest.TestCase):
    def test_energy_health(self):
        self.assertAlmostEqual(
            lim.health({"energy_full": 55000000, "energy_full_design": 60000000}),
            91.6667, places=2)

    def test_charge_fallback(self):
        self.assertAlmostEqual(
            lim.health({"charge_full": 6000000, "charge_full_design": 6500000}),
            92.3077, places=2)

    def test_health_none(self):
        self.assertIsNone(lim.health({}))
        self.assertIsNone(lim.health({"energy_full": 0, "energy_full_design": 0}))

    def test_grade(self):
        self.assertEqual(lim.battery_health_grade(95), "Excellent")
        self.assertEqual(lim.battery_health_grade(85), "Good")
        self.assertEqual(lim.battery_health_grade(75), "Fair")
        self.assertEqual(lim.battery_health_grade(60), "Poor")
        self.assertEqual(lim.battery_health_grade(30), "Critical")
        self.assertEqual(lim.battery_health_grade(None), "unknown")


class EstimateTests(unittest.TestCase):
    def test_discharging(self):
        d = {"status": "Discharging", "energy_now": 40000000,
             "energy_full": 55000000, "power_now": -13500000}
        self.assertAlmostEqual(lim.estimate(d), 40000000 * 3600 / 13500000, places=2)

    def test_charging(self):
        d = {"status": "Charging", "energy_now": 40000000,
             "energy_full": 55000000, "power_now": 13500000}
        self.assertAlmostEqual(lim.estimate(d), 15000000 * 3600 / 13500000, places=2)

    def test_no_estimate_cases(self):
        self.assertIsNone(lim.estimate({"status": "Discharging", "energy_now": 0, "power_now": 1}))
        self.assertIsNone(lim.estimate({"status": "Discharging", "energy_now": 1, "power_now": 0}))
        self.assertIsNone(lim.estimate({"status": "Full", "energy_now": 1, "power_now": 1}))


class FormatTests(unittest.TestCase):
    def test_fmt_energy(self):
        self.assertEqual(lim.fmt_energy(55000000), "55.00 Wh")

    def test_fmt_power(self):
        self.assertEqual(lim.fmt_power(-13500000), "-13.50 W")
        self.assertEqual(lim.fmt_power(250000), "250 mW")

    def test_fmt_voltage(self):
        self.assertEqual(lim.fmt_voltage(11560000), "11.560 V")

    def test_fmt_current(self):
        self.assertEqual(lim.fmt_current(-1234000), "-1.23 A")
        self.assertEqual(lim.fmt_current(750000), "750 mA")

    def test_fmt_duration(self):
        self.assertEqual(lim.fmt_duration(3600 + 120 + 3), "01:02:03")
        self.assertEqual(lim.fmt_duration(None), "n/a")

    def test_bar(self):
        self.assertEqual(len(lim.bar(50)), 24)
        self.assertEqual(lim.bar(0), "░" * 24)
        self.assertEqual(lim.bar(100), "█" * 24)


class SysfsTests(unittest.TestCase):
    def test_find_and_collect(self):
        with tempfile.TemporaryDirectory() as td:
            make_fake_battery(td)
            lim.POWER_SUPPLY = Path(td)
            bat = lim.find_battery()
            self.assertIsNotNone(bat)
            d = lim.collect(bat)
            self.assertEqual(d["capacity"], 75)
            self.assertEqual(d["status"], "Discharging")
            self.assertEqual(d["manufacturer"], "LENOVO")
            self.assertEqual(d["cycle_count"], 120)
            self.assertEqual(d["temp"], 312)
            self.assertAlmostEqual(lim.health(d), 55000000 / 60000000 * 100, places=2)

    def test_no_battery(self):
        with tempfile.TemporaryDirectory() as td:
            lim.POWER_SUPPLY = Path(td)
            self.assertIsNone(lim.find_battery())


if __name__ == "__main__":
    unittest.main()
