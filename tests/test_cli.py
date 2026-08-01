import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "li-monitoring.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lim = load_module(SCRIPT, "li_monitoring")


class CliTests(unittest.TestCase):
    def test_version_output(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), "--version"],
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertIn(lim.APP_VERSION, out.stdout)

    def test_json_output(self):
        with tempfile.TemporaryDirectory() as td:
            b = Path(td) / "BAT0"
            b.mkdir()
            (b / "type").write_text("Battery\n")
            (b / "capacity").write_text("66\n")
            (b / "status").write_text("Charging\n")
            old_sys, old_ps = sys.argv, lim.POWER_SUPPLY
            sys.argv = ["li-monitoring", "--json"]
            lim.POWER_SUPPLY = Path(td)
            try:
                buf = StringIO()
                with redirect_stdout(buf):
                    lim.main()
                data = json.loads(buf.getvalue())
            finally:
                sys.argv, lim.POWER_SUPPLY = old_sys, old_ps
        self.assertEqual(data["capacity"], 66)
        self.assertEqual(data["status"], "Charging")

    def test_no_battery_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as td:
            old_sys, old_ps = sys.argv, lim.POWER_SUPPLY
            sys.argv = ["li-monitoring"]
            lim.POWER_SUPPLY = Path(td)
            try:
                with self.assertRaises(SystemExit) as cm:
                    with redirect_stdout(StringIO()):
                        lim.main()
            finally:
                sys.argv, lim.POWER_SUPPLY = old_sys, old_ps
        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
