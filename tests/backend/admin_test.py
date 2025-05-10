import unittest
from unittest.mock import patch
import sys
import os

# Setup path to import app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app import app

class ColorSchemeTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'

    def set_session(self, key, value):
        with self.client.session_transaction() as sess:
            sess[key] = value

    # ----------------------------
    # get_color_scheme_session
    # ----------------------------

    def test_get_color_scheme_session_user_id_saved(self):
        self.set_session('color_scheme', 'sky')
        response = self.client.get('/get_color_scheme_session')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'color_scheme': 'sky'})

    def test_get_color_scheme_session_user_id_not_saved(self):
        response = self.client.get('/get_color_scheme_session')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'color_scheme': 'default'})

    # ----------------------------
    # update_color_scheme
    # ----------------------------

    @patch('app.get_db')
    @patch('app.save_db')
    def test_update_color_scheme_user_id_saved(self, mock_save_db, mock_get_db):
        self.set_session('id', 'Alyssa')
        app.global_mode = "edit"

        mock_cursor = mock_get_db.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)

        response = self.client.post('/update_color_scheme', json={"colorScheme": "bubblegum"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["colorScheme"], "bubblegum")

    def test_update_color_scheme_user_id_not_saved(self):
        self.set_session('access_token', 'mock_token')
        app.global_mode = "edit"

        response = self.client.post('/update_color_scheme', json={"colorScheme": "sky"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "User not logged in"})

if __name__ == '__main__':
    unittest.main()
