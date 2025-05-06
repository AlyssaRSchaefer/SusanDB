import unittest
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock

import sys
import os

# Get the directory of the current test file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory of 'tests' (which should contain 'app.py')
parent_dir = os.path.dirname(os.path.dirname(current_dir))
# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)

from app import app

from fpdf import FPDF

class GenerateReportAPITestCase(unittest.TestCase):

    def setUp(self):
        # Create a temp dir for all our PDF outputs
        self.tempdir = tempfile.mkdtemp()
        self.client = app.test_client()
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'  # for sessions

    def tearDown(self):
        # Remove the temp dir and everything in it
        shutil.rmtree(self.tempdir)

    # mocks for get_students_by_ids
    def mock_get_students_by_ids(self, student_ids, selected_fields):
        mock_data = {
            "1": ["Alice", "10"],
            "2": ["Bob", "11"],
            "3": ["Charlie", "12"],
        }
        return [mock_data.get(sid) for sid in student_ids]

    def mock_get_students_by_ids_invalid(self, student_ids, selected_fields):
        # only "1" is valid here
        return [student_ids and ["Alice"]]

    @patch('app.webview')
    @patch('os.startfile')
    def test_generate_report_one_student_selected(self, mock_startfile, mock_webview):
        # mock the file dialog to point inside our tempdir
        mock_path = os.path.join(self.tempdir, "one.pdf")
        mock_webview.windows = [MagicMock()]
        mock_webview.windows[0].create_file_dialog.return_value = mock_path

        with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
            resp = self.client.post(
                '/generate_report?ids[]=1',
                json={"fields": ["Name", "Grade"]}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['report_path'], mock_path)
        mock_startfile.assert_called_once_with(mock_path)
        self.assertTrue(os.path.exists(mock_path))

    @patch('app.webview')
    @patch('os.startfile')
    def test_generate_report_multiple_students_selected(self, mock_startfile, mock_webview):
        mock_path = os.path.join(self.tempdir, "multi.pdf")
        mock_webview.windows = [MagicMock()]
        mock_webview.windows[0].create_file_dialog.return_value = mock_path

        with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
            resp = self.client.post(
                '/generate_report?ids[]=1&ids[]=2',
                json={"fields": ["Name"]}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['report_path'], mock_path)
        mock_startfile.assert_called_once_with(mock_path)
        self.assertTrue(os.path.exists(mock_path))

if __name__ == '__main__':
    unittest.main()
