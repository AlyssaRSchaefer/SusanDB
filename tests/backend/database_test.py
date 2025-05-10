import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Setup import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app import app

class DatabaseEndpointsTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    # ------------------------
    # /get_data
    # ------------------------

    def test_get_data_no_students(self):
        with patch('app.query_db') as mock_query:
            mock_query.return_value = []
            response = self.client.post('/get_data', json={})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [])

    def test_get_data_some_students(self):
        with patch('app.query_db') as mock_query:
            mock_query.return_value = [{'id': '1', 'name': 'Alice'}]
            response = self.client.post('/get_data', json={})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.get_json()), 1)

    # ------------------------
    # /get_fields
    # ------------------------

    def test_get_fields_no_columns(self):
        with patch('app.get_field_order') as mock_fields:
            mock_fields.return_value = []
            response = self.client.get('/get_fields')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [])

    def test_get_fields_some_columns(self):
        with patch('app.get_field_order') as mock_fields:
            mock_fields.return_value = ['first_name', 'last_name']
            response = self.client.get('/get_fields')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), ['first_name', 'last_name'])

    # ------------------------
    # /get_student_fields
    # ------------------------

    def test_get_student_fields_no_fields(self):
        with patch('app.get_all_fields') as mock_fields:
            mock_fields.return_value = []
            response = self.client.get('/get_student_fields')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [])

    def test_get_student_fields_some_fields(self):
        with patch('app.get_all_fields') as mock_fields:
            mock_fields.return_value = ["grade", "age"]
            response = self.client.get('/get_student_fields')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), ["grade", "age"])

    # ------------------------
    # /get_field_values
    # ------------------------

    def test_get_field_values_no_values(self):
        with patch('app.get_db') as mock_get_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_get_db.return_value.execute.return_value = mock_cursor

            response = self.client.post('/get_field_values', json={'field': 'grade'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [])

    def test_get_field_values_some_values(self):
        with patch('app.get_db') as mock_get_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [(10,), (11,), (12,)]
            mock_get_db.return_value.execute.return_value = mock_cursor

            response = self.client.post('/get_field_values', json={'field': 'grade'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [10, 11, 12])

    # ------------------------
    # /update_database_cell
    # ------------------------

    def test_update_database_cell_data_to_data(self):
        with patch('app.get_db') as mock_get_db, patch('app.save_db'):
            mock_cursor = MagicMock()
            mock_get_db.return_value.execute.return_value = mock_cursor

            response = self.client.post('/update_database_cell', json={
                'id': '1', 'field': 'grade', 'newValue': '11'
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["message"], "Student data updated successfully.")

    def test_update_database_cell_empty_to_data(self):
        with patch('app.get_db') as mock_get_db, patch('app.save_db'):
            mock_cursor = MagicMock()
            mock_get_db.return_value.execute.return_value = mock_cursor

            response = self.client.post('/update_database_cell', json={
                'id': '2', 'field': 'notes', 'newValue': 'Good student'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn("Student data updated successfully", response.get_json()["message"])

    def test_update_database_cell_data_to_empty(self):
        with patch('app.get_db') as mock_get_db, patch('app.save_db'):
            mock_cursor = MagicMock()
            mock_get_db.return_value.execute.return_value = mock_cursor

            response = self.client.post('/update_database_cell', json={
                'id': '3', 'field': 'notes', 'newValue': ''
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn("Student data updated successfully", response.get_json()["message"])

    # ------------------------
    # /delete_students_from_db
    # ------------------------

    def test_delete_students_one_selected(self):
        with patch('app.get_db') as mock_get_db, patch('app.save_db'):
            mock_get_db.return_value.execute.return_value.rowcount = 1
            response = self.client.post('/delete_students_from_db', json={"ids": ["1"]})
            self.assertEqual(response.status_code, 200)
            self.assertIn("Students deleted successfully", response.get_json()["message"])

    def test_delete_students_multiple_selected(self):
        with patch('app.get_db') as mock_get_db, patch('app.save_db'):
            mock_get_db.return_value.execute.return_value.rowcount = 2
            response = self.client.post('/delete_students_from_db', json={"ids": ["1", "2"]})
            self.assertEqual(response.status_code, 200)
            self.assertIn("Students deleted successfully", response.get_json()["message"])

    def test_delete_students_none_selected(self):
        response = self.client.post('/delete_students_from_db', json={"ids": []})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "No student IDs provided")

if __name__ == '__main__':
    unittest.main()
