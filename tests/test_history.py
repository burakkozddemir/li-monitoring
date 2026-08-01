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


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        lim.DATA_DIR = Path(self.tmp.name)
        lim.LOG_FILE = lim.DATA_DIR / "history.jsonl"

    def test_append_and_load(self):
        lim.append_history({"capacity": 50, "status": "Discharging", "ts": "2026-08-01T00:00:00"})
        rows = lim.load_history()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["capacity"], 50)

    def test_load_ignores_bad_lines(self):
        lim.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with lim.LOG_FILE.open("w") as f:
            f.write('{"capacity": 10}\n')
            f.write("not-json\n")
            f.write("\n")
            f.write('{"capacity": 20}\n')
        rows = lim.load_history()
        self.assertEqual([r["capacity"] for r in rows], [10, 20])

    def test_trim_history(self):
        with lim.LOG_FILE.open("w") as f:
            for i in range(10500):
                f.write(json.dumps({"i": i, "pad": "x" * 190}) + "\n")
        lim.append_history({"i": -1, "pad": "x" * 190})
        rows = lim.load_history()
        self.assertEqual(len(rows), 10000)
        self.assertEqual(rows[-1]["i"], -1)
        self.assertEqual(rows[0]["i"], 501)


if __name__ == "__main__":
    unittest.main()
