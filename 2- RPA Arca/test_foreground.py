import unittest
from unittest.mock import Mock
from main import ArcaApp

class ForegroundTests(unittest.TestCase):
    def test_restore_and_release_temporary_topmost(self):
        app = ArcaApp.__new__(ArcaApp)
        app.root = Mock()
        app._bring_to_front()
        app.root.deiconify.assert_called_once()
        app.root.lift.assert_called_once()
        app.root.focus_force.assert_called_once()
        app.root.attributes.assert_called_with('-topmost', True)
        delay, release = app.root.after.call_args.args
        self.assertLessEqual(delay, 1000)
        release()
        app.root.attributes.assert_called_with('-topmost', False)
