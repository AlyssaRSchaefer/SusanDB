# import unittest
# from unittest.mock import patch, MagicMock
# from flask import Flask
# import json
# import os
# import sys
# from datetime import datetime

# # Get the directory of the current test file
# current_dir = os.path.dirname(os.path.abspath(__file__))
# # Get the parent directory of 'tests' (which should contain 'app.py')
# parent_dir = os.path.dirname(os.path.dirname(current_dir))
# # Add the parent directory to sys.path
# sys.path.insert(0, parent_dir)

# from app import app  # Import your Flask app
# from fpdf import FPDF

# class GenerateReportAPITestCase(unittest.TestCase):

#     def setUp(self):
#         self.client = app.test_client()
#         app.config['TESTING'] = True
#         app.config['SECRET_KEY'] = 'test_secret_key' # Required for sessions

#     def tearDown(self):
#         pass

#     def mock_get_students_by_ids(self, student_ids, selected_fields):
#         mock_data = {
#             "1": ["Alice", "10"],
#             "2": ["Bob", "11"],
#             "3": ["Charlie", "12"],
#         }
#         return [mock_data.get(sid) for sid in student_ids if sid in mock_data]

#     def mock_get_students_by_ids_long_value(self, student_ids, selected_fields):
#         mock_data = {
#             "1": ["This is a veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery long value"],
#         }
#         return [mock_data.get(sid) for sid in student_ids if sid in mock_data]

#     def mock_get_students_by_ids_invalid(self, student_ids, selected_fields):
#         mock_data = {
#             "1": ["Alice"],
#             "3": ["Charlie"],
#         }
#         return [mock_data.get(sid) for sid in student_ids if sid in mock_data]

#     @patch('app.webview')
#     @patch('os.startfile')
#     def test_generate_report_one_student_selected(self, mock_startfile, mock_webview):
#         mock_file_path = "/tmp/test_report_one.pdf"
#         mock_webview.windows = [MagicMock()]
#         mock_webview.windows[0].create_file_dialog.return_value = mock_file_path

#         with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
#             response = self.client.post('/generate_report?ids[]=1', json={"fields": ["Name", "Grade"]})
#             self.assertEqual(response.status_code, 200)
#             data = response.get_json()
#             self.assertTrue(data['success'])
#             self.assertEqual(data['message'], "Report generated successfully")
#             self.assertEqual(data['report_path'], mock_file_path)
#             mock_webview.windows[0].create_file_dialog.assert_called_once()
#             mock_startfile.assert_called_once_with(mock_file_path)
#             self.assertTrue(os.path.exists(mock_file_path))
#             os.remove(mock_file_path)

#     @patch('app.webview')
#     @patch('os.startfile')
#     def test_generate_report_multiple_students_selected(self, mock_startfile, mock_webview):
#         mock_file_path = "/tmp/test_report_multiple.pdf"
#         mock_webview.windows = [MagicMock()]
#         mock_webview.windows[0].create_file_dialog.return_value = mock_file_path

#         with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
#             response = self.client.post('/generate_report?ids[]=1&ids[]=2', json={"fields": ["Name"]})
#             self.assertEqual(response.status_code, 200)
#             data = response.get_json()
#             self.assertTrue(data['success'])
#             self.assertEqual(data['message'], "Report generated successfully")
#             self.assertEqual(data['report_path'], mock_file_path)
#             mock_webview.windows[0].create_file_dialog.assert_called_once()
#             mock_startfile.assert_called_once_with(mock_file_path)
#             self.assertTrue(os.path.exists(mock_file_path))
#             os.remove(mock_file_path)

#     @patch('app.webview')
#     @patch('os.startfile')
#     def test_generate_report_only_valid_student_ids_passed(self, mock_startfile, mock_webview):
#         mock_file_path = "/tmp/test_report_valid_ids.pdf"
#         mock_webview.windows = [MagicMock()]
#         mock_webview.windows[0].create_file_dialog.return_value = mock_file_path

#         with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
#             response = self.client.post('/generate_report?ids[]=1&ids[]=3', json={"fields": ["Name"]})
#             self.assertEqual(response.status_code, 200)
#             data = response.get_json()
#             self.assertTrue(data['success'])
#             self.assertEqual(data['message'], "Report generated successfully")
#             self.assertEqual(data['report_path'], mock_file_path)
#             mock_webview.windows[0].create_file_dialog.assert_called_once()
#             mock_startfile.assert_called_once_with(mock_file_path)
#             self.assertTrue(os.path.exists(mock_file_path))
#             os.remove(mock_file_path)

#     @patch('app.webview')
#     @patch('os.startfile')
#     def test_generate_report_invalid_student_id_passed(self, mock_startfile, mock_webview):
#         mock_file_path = "/tmp/test_report_invalid_id.pdf"
#         mock_webview.windows = [MagicMock()]
#         mock_webview.windows[0].create_file_dialog.return_value = mock_file_path

#         with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids_invalid):
#             response = self.client.post('/generate_report?ids[]=1&ids[]=99', json={"fields": ["Name"]})
#             self.assertEqual(response.status_code, 200)
#             data = response.get_json()
#             self.assertTrue(data['success'])
#             self.assertEqual(data['message'], "Report generated successfully")
#             self.assertEqual(data['report_path'], mock_file_path)
#             mock_webview.windows[0].create_file_dialog.assert_called_once()
#             mock_startfile.assert_called_once_with(mock_file_path)
#             self.assertTrue(os.path.exists(mock_file_path))
#             os.remove(mock_file_path)

#     @patch('app.webview')
#     @patch('os.startfile')
#     def test_generate_report_title_passed(self, mock_startfile, mock_webview):
#         mock_file_path = "/tmp/test_report_title.pdf"
#         mock_webview.windows = [MagicMock()]
#         mock_webview.windows[0].create_file_dialog.return_value = mock_file_path

#         with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
#             response = self.client.post('/generate_report?ids[]=1', json={"fields": ["Name"], "title": "Custom Report Title"})
#             self.assertEqual(response.status_code, 200)
#             data = response.get_json()
#             self.assertTrue(data['success'])
#             self.assertEqual(data['message'], "Report generated successfully")
#             self.assertEqual(data['report_path'], mock_file_path)
#             mock_webview.windows[0].create_file_dialog.assert_called_once()
#             mock_startfile.assert_called_once_with(mock_file_path)
#             self.assertTrue(os.path.exists(mock_file_path))

#             # Basic check for title in PDF content
#             with open(mock_file_path, 'rb') as f:
#                 pdf_content = f.read().decode('latin-1')
#                 self.assertIn("Custom Report Title", pdf_content)
#             os.remove(mock_file_path)

#     @patch('app.webview')
#     @patch('os.startfile')
#     def test_generate_report_title_not_passed(self, mock_startfile, mock_webview):
#         mock_file_path = "/tmp/test_report_no_title.pdf"
#         mock_webview.windows = [MagicMock()]
#         mock_webview.windows[0].create_file_dialog.return_value = mock_file_path

#         with patch('app.get_students_by_ids', side_effect=self.mock_get_students_by_ids):
#             response = self.client.post('/generate_report?ids[]=1', json={"fields": ["Name"]})
#             print(response.data.decode('utf-8'))
#             self.assertEqual(response.status_code, 200)
#             data = response.get_json()
#             self.assertTrue(data['success'])
#             self.assertEqual(data['message'], "Report generated successfully")
#             self.assertEqual(data['report_path'], mock_file_path)
#             mock_webview.windows[0].create_file_dialog.assert_called_once()
#             mock_startfile.assert_called_once_with(mock_file_path)
#             self.assertTrue(os.path.exists(mock_file_path))

#             # Basic check for absence of a specific custom title
#             with open(mock_file_path, 'rb') as f:
#                 pdf_content = f.read().decode('latin-1')
#                 # Assuming no specific title string is used if not passed
#                 pass
#             os.remove(mock_file_path)