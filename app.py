import msal
import threading
import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify
import webview

# Load environment variables from .env file
load_dotenv()

# Flask app setup
app = Flask(__name__)

# Constants for Azure app registration loaded from environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTHORITY = os.getenv('AUTHORITY')
SCOPE = os.getenv('SCOPE').split(',')
REDIRECT_URI = os.getenv('REDIRECT_URI')
API_VERSION = os.getenv('API_VERSION')

# MSAL (Microsoft Authentication Library) app setup
def _build_msal_app():
    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )

# Flask route to initiate the login process
@app.route('/')
def index():
    msal_app = _build_msal_app()
    # Get the authorization URL
    auth_url = msal_app.get_authorization_request_url(SCOPE, redirect_uri=REDIRECT_URI)
    
    # Redirect the user to the Microsoft login page
    return redirect(auth_url)

# Flask route to handle the OAuth2 callback
@app.route('/get_token')
def get_token():
    msal_app = _build_msal_app()
    # Extract the authorization code from the request
    code = request.args.get('code')

    if not code:
        return "Authorization code is missing", 400

    # Exchange the authorization code for an access token
    result = msal_app.acquire_token_by_authorization_code(code, scopes=SCOPE, redirect_uri=REDIRECT_URI)
    
    if 'access_token' in result:
        # Successful authentication, display the access token
        return jsonify({'access_token': result['access_token']})
    else:
        # If failed, return the error response
        return jsonify(result), 400

# Function to start Flask server in a separate thread
def start_flask():
    app.run(port=5000)

# Function to start PyWebView for login
def start_webview():
    # Get the authorization URL from Flask
    auth_url = 'http://localhost:5000/'
    webview.create_window('Microsoft Login', auth_url)
    webview.start()

# Run Flask server and PyWebView in separate threads
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()
    
    # Start PyWebView window to initiate Microsoft login
    start_webview()
