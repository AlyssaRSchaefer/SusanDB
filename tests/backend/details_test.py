import unittest
from unittest.mock import patch
from flask import json
import sys
import os

# Setup path to import app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app import app

class TestDetailsPage(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.get_student_by_id')
    def test_get_student(self, mock_get_student):
        mock_get_student.return_value = {
            'first_name': 'Ada',
            'last_name': 'Lovelace',
            'email': 'ada@history.com',
            'major': 'Computer Science'
        }

        response = self.app.post('/get_student', json={'id': 'student123'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['first_name'], 'Ada')
        self.assertEqual(data['last_name'], 'Lovelace')
        self.assertEqual(data['email'], 'ada@history.com')
        self.assertEqual(data['major'], 'Computer Science')

    @patch('app.get_student_files')
    def test_get_student_files(self, mock_get_files):
        mock_get_files.return_value = ['essay.pdf', 'notes.txt']

        response = self.app.post('/get_student_files', json={'student_id': 'student123'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('essay.pdf', data['files'])
        self.assertIn('notes.txt', data['files'])

    @patch('app.update_database_cell')
    def test_update_database_cell(self, mock_update):
        mock_update.return_value = True

        response = self.app.post('/update_database_cell', json={
            'id': 'student123',
            'field': 'email',
            'newValue': 'newemail@example.com'
        })

        self.assertEqual(response.status_code, 200)

    @patch('app.delete_student_file')
    def test_delete_student_file(self, mock_delete):
        mock_delete.return_value = True

        response = self.app.post('/delete_student_file', json={
            'student_id': 'student123',
            'file_name': 'essay.pdf'
        })

        self.assertEqual(response.status_code, 200)

    @patch('app.download_student_file')
    def test_download_student_file(self, mock_download):
        mock_download.return_value = {'status': 'ok'}

        response = self.app.post('/download_student_file', json={
            'student_id': 'student123',
            'file_name': 'essay.pdf'
        })

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
