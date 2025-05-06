import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
import pandas as pd
from io import BytesIO
import json

import sys
import os

# Get the directory of the current test file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory of 'tests' (which should contain 'app.py')
parent_dir = os.path.dirname(os.path.dirname(current_dir))
# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)

from app import app

class DataUpdateAPITestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.application.config['TESTING'] = True

        # Mock OneDrive interaction functions
        self.mock_download_onedrive = patch('app.download_file_from_file_name', return_value=b'mock_excel_content').start()
        self.mock_upload_onedrive = patch('app.update_file_from_file_name', return_value=True).start()

    def tearDown(self):
        self.mock_download_onedrive.stop()
        self.mock_upload_onedrive.stop()

    def mock_get_db(self):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_db.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        mock_cursor.rowcount = 0
        return mock_db

    def mock_pd_read_excel(self, *args, **kwargs):
        data = {'student_id_excel': [1, 2, 3], 'name_excel': ['Alice', 'Bob', 'Charlie'], 'grade_excel': [10, 11, 12]}
        return pd.DataFrame(data)

    def test_generate_preview_all_ids_in_db(self):
        with self.app.session_transaction() as sess:
            sess['access_token'] = 'test_access_token'

            with patch('app.pd.read_excel', side_effect=self.mock_pd_read_excel):
                with patch('app.get_db', return_value=self.mock_get_db()) as mock_db_func:
                    mock_db = mock_db_func.return_value
                    mock_cursor = mock_db.cursor.return_value
                    mock_cursor.fetchone.side_effect = [
                        (1, 'Existing', 'Alice', 10),
                        (2, 'Existing', 'Bob', 11),
                        (3, 'Existing', 'Charlie', 12),
                    ]

                    data = {
                        'selectedExcelFields': ['name_excel', 'grade_excel'],
                        'selectedSusanDBFields': ['first_name', 'grade'],
                        'mappingRules': [{'excel': ['student_id_excel'], 'susandb': ['student_id']}]
                    }
                    response = self.app.post('/generate_preview', json=data)
                    self.assertEqual(response.status_code, 200)
                    preview_data = response.get_json()['preview']
                    self.assertEqual(len(preview_data), 3)
                    for item in preview_data:
                        self.assertIn('student_id', item)
                        self.assertIn('changes', item)

    def test_generate_preview_one_id_not_in_db(self):
        with self.app.session_transaction() as sess:
            sess['access_token'] = 'test_access_token'

            with patch('app.pd.read_excel', side_effect=self.mock_pd_read_excel):
                with patch('app.get_db', return_value=self.mock_get_db()) as mock_db_func:
                    mock_db = mock_db_func.return_value
                    mock_cursor = mock_db.cursor.return_value
                    mock_cursor.fetchone.side_effect = [
                        (1, 'Existing', 'Alice', 10),
                        None,
                        (3, 'Existing', 'Charlie', 12),
                    ]

                    data = {
                        'selectedExcelFields': ['name_excel', 'grade_excel'],
                        'selectedSusanDBFields': ['first_name', 'grade'],
                        'mappingRules': [{'excel': ['student_id_excel'], 'susandb': ['student_id']}]
                    }
                    response = self.app.post('/generate_preview', json=data)
                    self.assertEqual(response.status_code, 200)
                    preview_data = response.get_json()['preview']
                    self.assertEqual(len(preview_data), 2)
                    student_ids_in_preview = [item['student_id'] for item in preview_data]
                    self.assertIn(1, student_ids_in_preview)
                    self.assertNotIn(2, student_ids_in_preview)
                    self.assertIn(3, student_ids_in_preview)

    def test_update_db_from_excel_all_ids_in_db(self):
        with self.app.session_transaction() as sess:
            sess['access_token'] = 'test_access_token'

        with patch('app.get_db', return_value=self.mock_get_db()) as mock_db_func:
            with patch('app.save_db') as mock_save_db: # Mock save_db
                mock_db = mock_db_func.return_value
                mock_cursor = mock_db.cursor.return_value
                mock_cursor.rowcount = 1

                data = {
                    'updates': [
                        {'student_id': 1, 'changes': [{'field': 'first_name', 'new_value': 'Updated Alice'}]},
                        {'student_id': 2, 'changes': [{'field': 'grade', 'new_value': 12}]},
                        {'student_id': 3, 'changes': []},
                    ]
                }
                response = self.app.post('/update_db_from_excel', json=data)
                print(response.data.decode('utf-8')) # Decode the response data
                self.assertEqual(response.status_code, 200)
                response_data = response.get_json()
                self.assertIn('message', response_data)
                self.assertIn('Database update completed. 2 changes applied successfully.', response_data['message'])
                self.assertEqual(mock_db.execute.call_count, 2)
                mock_save_db.assert_called_once() # Ensure save_db was called