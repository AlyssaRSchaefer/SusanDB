# import unittest
# from unittest.mock import patch, MagicMock
# from flask import Flask, session, redirect, url_for, render_template, Response
# import os
# import sys

# # Get the directory of the current test file
# current_dir = os.path.dirname(os.path.abspath(__file__))
# # Get the parent directory of 'tests' (which should contain 'app.py')
# parent_dir = os.path.dirname(os.path.dirname(current_dir))
# # Add the parent directory to sys.path
# sys.path.insert(0, parent_dir)

# from app import app, msal_app, SCOPES, check_lock_file, create_lock_file, set_mode, generic_logout_functions
# from datetime import datetime

# class AuthLogoutAPITestCase(unittest.TestCase):

#     def setUp(self):
#         self.client = app.test_client()  # Create the test client directly
#         app.config['TESTING'] = True
#         app.config['SECRET_KEY'] = 'test_secret_key' # Required for sessions

#     def tearDown(self):
#         pass

#     def mock_msal_acquire_token_interactive(self, SCOPES):
#         return {"access_token": "mock_access_token"}

#     def mock_msal_acquire_token_interactive_failure(self, SCOPES):
#         return {"error": "invalid_grant", "error_description": "Failed to acquire token"}

#     def mock_check_lock_file_exists(self):
#         # Return integer timestamp string
#         timestamp = int(datetime.now().timestamp())
#         return (str(timestamp), "test_user")

#     def mock_check_lock_file_not_exists(self):
#         return None

#     def mock_create_lock_file(self):
#         pass

#     def mock_set_mode(self, mode):
#         pass

#     def mock_generic_logout_functions(self):
#         pass

#     def test_loginOnedrive_shared_with_user(self):
#         with patch('app.msal_app.acquire_token_interactive', side_effect=self.mock_msal_acquire_token_interactive):
#             with patch('app.check_lock_file', side_effect=self.mock_check_lock_file_exists):
#                 with patch('app.run_at_login') as mock_run_at_login:
#                     with patch('app.webview') as mock_webview:
#                         mock_webview.windows = [MagicMock()]
#                         response = self.client.get('/login')
#                         self.assertEqual(response.status_code, 200)
#                         self.assertIn(b"Last accessed by", response.data) # Unique content in lockfile_exists.html
#                         self.assertIn(b"test_user", response.data)
#                         self.assertIn(b"access_token", session)
#                         self.assertEqual(session["access_token"], "mock_access_token")
#                         mock_run_at_login.assert_called_once()
#                         mock_webview.windows[0].maximize.assert_called_once()

#     def test_loginOnedrive_not_shared_with_user(self):
#         with patch('app.msal_app.acquire_token_interactive', side_effect=self.mock_msal_acquire_token_interactive):
#             with patch('app.check_lock_file', side_effect=self.mock_check_lock_file_not_exists):
#                 with patch('app.create_lock_file') as mock_create_lock_file:
#                     with patch('app.set_mode') as mock_set_mode:
#                         with patch('app.run_at_login') as mock_run_at_login:
#                             with patch('app.webview') as mock_webview:
#                                 mock_webview.windows = [MagicMock()]
#                                 response = self.client.get('/login')
#                                 self.assertEqual(response.status_code, 200)
#                                 self.assertIn(b"GENERATE REPORT", response.data) # Unique content in database.html
#                                 self.assertIn(b"access_token", session)
#                                 self.assertEqual(session["access_token"], "mock_access_token")
#                                 mock_create_lock_file.assert_called_once()
#                                 mock_set_mode.assert_called_once_with("edit")
#                                 mock_run_at_login.assert_called_once()
#                                 mock_webview.windows[0].maximize.assert_called_once()

#     def test_loginOnedrive_login_failure(self):
#         with self.client as client: # Use self.client
#             with patch('app.msal_app.acquire_token_interactive', side_effect=self.mock_msal_acquire_token_interactive_failure):
#                 response = client.get('/login')
#                 self.assertIn(b"Login failed: Failed to acquire token", response.data)
#                 self.assertNotIn("access_token", session)

#     def test_logoutUser_logs_out(self):
#         with self.client as client: # Use self.client
#             with client.session_transaction() as sess:
#                 sess['access_token'] = 'mock_access_token'

#             with patch('app.generic_logout_functions') as mock_logout:
#                 response = client.get('/logout', follow_redirects=True)
#                 self.assertEqual(response.status_code, 200)
#                 self.assertNotIn("access_token", session)
#                 mock_logout.assert_called_once()
#                 self.assertIn(b"index.html", response.data) # Adjust if your redirect target is different

#     def test_logoutUser_exits_program_through_x(self):
#         with self.client as client: # Use self.client
#             with client.session_transaction() as sess:
#                 sess['access_token'] = 'mock_access_token'

#             with patch('app.generic_logout_functions') as mock_logout:
#                 with patch('app.webview') as mock_webview:
#                     mock_webview.windows = [MagicMock()]
#                     response = client.get('/logout_from_x')
#                     self.assertEqual(response.status_code, 204) # No Content
#                     self.assertNotIn("access_token", session)
#                     mock_logout.assert_called_once()
#                     mock_webview.windows[0].destroy.assert_called_once()