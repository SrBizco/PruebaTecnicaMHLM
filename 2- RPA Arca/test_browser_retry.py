import threading
import unittest
from queue import Queue
from unittest.mock import Mock, patch
import arca_browser as browser

class ServicesRetryTests(unittest.TestCase):
    def test_validation_failure_keeps_session_and_allows_retry(self):
        context, page = Mock(), Mock()
        page.is_closed.return_value = False
        context.pages = [page]
        action, finish = threading.Event(), threading.Event()
        messages = Queue()
        action.set()
        with patch.object(browser, '_wait_for_action', return_value=page), patch.object(browser, '_open_services', return_value=page), patch.object(browser, '_extract_visible_services', side_effect=[browser.WorkflowError('No se reconocio la pagina.'), ['Servicio de prueba']]):
            result = browser._wait_for_services(context, page, action, finish, messages)
        self.assertEqual(result, ['Servicio de prueba'])
        self.assertFalse(action.is_set())
        self.assertEqual(messages.get_nowait()[0], 'ready_services')
        context.close.assert_not_called()
        page.close.assert_not_called()

    def test_cancel_does_not_extract(self):
        with patch.object(browser, '_wait_for_action', return_value=None), patch.object(browser, '_extract_visible_services') as extract:
            finish = threading.Event()
            finish.set()
            result = browser._wait_for_services(Mock(), Mock(), threading.Event(), finish, Queue())
        self.assertIsNone(result)
        extract.assert_not_called()

if __name__ == '__main__':
    unittest.main()
