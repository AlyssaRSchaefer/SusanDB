import os
import logging
from dotenv import load_dotenv
import msal
import webview
import threading
from flask import Flask, render_template
import requests

# Configure logging
# logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

app = Flask(__name__)  # Flask app (needed for other potential endpoints)
app.secret_key = os.getenv("SESSION_SECRET")
access_token = False

# Configuration from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = os.getenv("AUTHORITY")
SCOPES = os.getenv("SCOPE").split(",")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Should be msauth://redirect

if not all([CLIENT_ID, AUTHORITY, SCOPES, REDIRECT_URI, app.secret_key]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# MSAL app setup
def _build_msal_app():
    return msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )

msal_app = _build_msal_app()

def login():
    with app.app_context():  # Ensure Flask's application context is available
        result = msal_app.acquire_token_interactive(SCOPES)

        if "access_token" in result:
            access_token = result.get("access_token")
            user_data = get_user_profile(access_token)
            return render_template("profile.html", access_token=user_data)
        else:
            return f"Login failed: {result.get('error_description', 'Unknown error')}"

def get_user_profile(access_token):
    # Microsoft Graph API endpoint for User.Read
    url = "https://graph.microsoft.com/v1.0/me"

    # Authorization header with the access token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Make the GET request
    response = requests.get(url, headers=headers)

    # Check if the response is successful
    if response.status_code == 200:
        user_data = response.json()
        return user_data
    else:
        return f"Error: {response.status_code} - {response.text}"


# Function to start PyWebView for login
def start_webview():
    webview.create_window('Microsoft Login', html=login())
    webview.start()

# Function to start Flask server in a separate thread
def start_flask():
    app.run(port=5000)

# Run Flask server and PyWebView in separate threads
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()
    
    # Start PyWebView window to initiate Microsoft login
    start_webview()