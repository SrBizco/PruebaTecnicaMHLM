import unittest
from unittest.mock import patch
import pywintypes
import credential_store as store

class CredentialErrors(unittest.TestCase):
    def test_empty_profiles(self):
        with patch.object(store._win32cred(), 'CredEnumerate', side_effect=pywintypes.error(1168, 'CredEnumerate', 'test')):
            self.assertEqual(store.list_profiles(), [])

    def test_permission_error(self):
        with patch.object(store._win32cred(), 'CredEnumerate', side_effect=pywintypes.error(5, 'CredEnumerate', 'test')):
            with self.assertRaises(store.CredentialStoreError):
                store.list_profiles()

    def test_delete_missing(self):
        with patch.object(store._win32cred(), 'CredDelete', side_effect=pywintypes.error(1168, 'CredDelete', 'test')) as delete:
            store.delete_profile(store.Profile('0' * 32, 'Test', '00000000000'))
            self.assertEqual(delete.call_count, 2)

    def test_delete_denied_keeps_metadata(self):
        with patch.object(store._win32cred(), 'CredDelete', side_effect=pywintypes.error(5, 'CredDelete', 'test')) as delete:
            with self.assertRaises(store.CredentialStoreError):
                store.delete_profile(store.Profile('0' * 32, 'Test', '00000000000'))
            self.assertEqual(delete.call_count, 1)

if __name__ == '__main__':
    unittest.main()
