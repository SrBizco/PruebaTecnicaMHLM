import unittest
import os
from pathlib import Path
from unittest.mock import patch
from launcher import prepare

class SetupTests(unittest.TestCase):
    def test_existing_browser_not_downloaded(self):
        with patch('launcher.check_runtime',return_value=True), patch('launcher.install_browser') as install:
            prepare(lambda message: None)
        install.assert_not_called()

    def test_missing_browser_installed_and_checked(self):
        with patch('launcher.check_runtime',side_effect=[False, True]) as check, patch('launcher.install_browser') as install:
            prepare(lambda message: None)
        install.assert_called_once()
        self.assertEqual(check.call_count,2)

    def test_failed_download_propagates(self):
        with patch('launcher.check_runtime',return_value=False), patch('launcher.install_browser',side_effect=RuntimeError('Descarga fallida')):
            with self.assertRaises(RuntimeError):
                prepare(lambda message: None)

    def test_no_override_uses_persistent_cache(self):
        from launcher import configure_browser_path
        with patch.dict(os.environ, {"LOCALAPPDATA": "C:/FakeUser/Local"}, clear=True):
            configure_browser_path()
            self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"], str(Path("C:/FakeUser/Local") / "ms-playwright"))

    def test_frozen_zero_path_is_replaced(self):
        from launcher import configure_browser_path
        with patch.dict(os.environ, {"LOCALAPPDATA": "C:/FakeUser/Local", "PLAYWRIGHT_BROWSERS_PATH": "0"}, clear=True):
            configure_browser_path()
            self.assertNotEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"], "0")
