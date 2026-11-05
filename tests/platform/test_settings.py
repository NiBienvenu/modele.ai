"""Tests of the configuration layer. No torch needed.

Run:  python -m unittest discover -s tests/platform -t .
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from config.env import load_env_file, parse_env_line
from config.settings import PROJECT_ROOT, Settings


class ParseEnvLineTest(unittest.TestCase):
    def test_simple_value(self):
        self.assertEqual(parse_env_line("PORT=8000"), ("PORT", "8000"))

    def test_quotes_are_removed(self):
        self.assertEqual(parse_env_line('NAME="a b"'), ("NAME", "a b"))

    def test_comments_and_blank_lines_are_ignored(self):
        self.assertIsNone(parse_env_line("# comment"))
        self.assertIsNone(parse_env_line("   "))

    def test_value_can_contain_equal_sign(self):
        self.assertEqual(parse_env_line("TOKEN=a=b"), ("TOKEN", "a=b"))


class LoadEnvFileTest(unittest.TestCase):
    def test_real_environment_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("PORT=1111\nHOST=example\n")
            with mock.patch.dict(os.environ, {"PORT": "2222"}, clear=True):
                load_env_file(env_file)
                self.assertEqual(os.environ["PORT"], "2222")
                self.assertEqual(os.environ["HOST"], "example")


class SettingsTest(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.server.port, 8000)
        self.assertEqual(settings.model.device, "auto")
        self.assertEqual(settings.model.path, PROJECT_ROOT / "models" / settings.model.name)
        self.assertIsNone(settings.model.quantize)

    def test_empty_values_fall_back_to_defaults(self):
        with mock.patch.dict(os.environ, {"MODEL_PATH": "", "TOP_K": "", "QUANTIZE": ""}, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.model.path, PROJECT_ROOT / "models" / settings.model.name)
        self.assertIsNone(settings.generation.top_k)

    def test_values_from_environment(self):
        env = {"MODEL_PATH": "/data/m", "TOP_K": "40", "CORS_ORIGINS": "http://a, http://b", "DEVICE": "cpu"}
        with mock.patch.dict(os.environ, env, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.model.path, Path("/data/m"))
        self.assertEqual(settings.generation.top_k, 40)
        self.assertEqual(settings.server.cors_origins, ["http://a", "http://b"])
        self.assertEqual(settings.model.device, "cpu")


if __name__ == "__main__":
    unittest.main()
