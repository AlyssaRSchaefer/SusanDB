import unittest
from unittest.mock import patch
import sys
import os

# Setup import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app import app

class SaveFieldsTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    @patch('app.upload_file_to_onedrive')
    def test_save_fields_with_valid_fields(self, mock_upload):
        mock_upload.return_value = True
        fields = ["first_name", "last_name", "grade"]

        response = self.client.post('/save_fields', json={"fields": fields})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"message": "Field order successfully updated."})
        mock_upload.assert_called_once()

    def test_save_fields_with_no_fields(self):
        response = self.client.post('/save_fields', json={"fields": None})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "Invalid data format. Expected a list."})

if __name__ == '__main__':
    unittest.main()
