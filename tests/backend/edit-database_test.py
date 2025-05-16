import unittest
from unittest.mock import patch
import sys
import os
import json

# Setup path to import app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app import app

class EditDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.secret_key = 'test_secret'  # Ensure session works
        self.client = app.test_client()

        with self.client.session_transaction() as sess:
            sess['user'] = 'testuser'


    def login(self):
        with self.client.session_transaction() as sess:
            sess['user'] = 'testuser'

    def test_add_field_success(self):
        self.login() 
        response = self.client.post('/add_field_to_db', json={
            "field": "email",
            "default": "",
            "addToLayout": False
        })
        self.assertEqual(response.status_code, 200)

    def test_add_field_not_logged_in(self):
        with self.client.session_transaction() as sess:
            sess.pop('user', None)  # Ensure no user is logged in
        response = self.client.post('/add_field_to_db', json={
            "field": "email",
            "default": "",
            "addToLayout": False
        })
        self.assertEqual(response.status_code, 403)

    def test_delete_field_success(self):
        self.login() 
        response = self.client.post('/delete_field_from_db', json={
            "field": "email"
        })
        self.assertEqual(response.status_code, 200)

    def test_delete_field_missing_field(self):
        response = self.client.post('/delete_field_from_db', json={})
        self.assertEqual(response.status_code, 400)

    def test_delete_field_not_logged_in(self):
        with self.client.session_transaction() as sess:
            sess.pop('user', None)
        response = self.client.post('/delete_field_from_db', json={
            "field": "email"
        })
        self.assertEqual(response.status_code, 403)

    def test_get_student_fields_success(self):
        self.login()
        response = self.client.get('/get_student_fields')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        field_list = data.get("fields") if isinstance(data, dict) else data
        expected_fields = {"first_name", "last_name", "email", "student_id"}
        self.assertTrue(expected_fields.issubset(set(field_list)))


    def test_get_student_fields_unsorted_success(self):
        self.login()
        response = self.client.get('/get_student_fields_unsorted')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        field_list = data.get("fields") if isinstance(data, dict) else data
        expected_unsorted_fields = {"last_name", "first_name", "student_id", "address", "email"}
        self.assertTrue(expected_unsorted_fields.issubset(set(field_list)))

if __name__ == '__main__':
    unittest.main()
