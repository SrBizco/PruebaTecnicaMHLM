import unittest
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
