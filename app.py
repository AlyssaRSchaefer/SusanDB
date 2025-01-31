import os
import logging
from dotenv import load_dotenv
import msal
import webview
import threading
from flask import Flask, render_template, request
import requests
import base64

# Configure logging (optional)
# logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET")

# Configuration from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = os.getenv("AUTHORITY")
SCOPES = ["Files.ReadWrite.All", "Files.ReadWrite.AppFolder"]
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Should be msauth://redirect

if not all([CLIENT_ID, AUTHORITY, SCOPES, REDIRECT_URI, app.secret_key]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# encode the sharing URL into a share ID that Graph API understands
def generate_share_id(sharing_url):
    base64_value = base64.b64encode(sharing_url.encode()).decode()
    share_id = "u!" + base64_value.rstrip("=").replace("/", "_").replace("+", "-")
    return share_id

# get all contents in shared folder
def list_shared_folder_contents(access_token, sharing_url):
    share_id = generate_share_id(sharing_url)
    url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/children"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        items = response.json().get("value", [])
        return items
    elif response.status_code == 403:
        # TODO: add handling for is status is unauthorized
        return None
    else:
        logging.error(f"Error listing folder contents: {response.status_code} {response.text}")
        return None

# download a file's content from OneDrive
def download_file(access_token, file_id):
    # Using the /content endpoint returns the raw bytes of the file
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        logging.error(f"Error downloading file: {response.status_code} {response.text}")
        return None

# reupload the file by PUT-ing the new content
def update_file(access_token, file_id, updated_content):
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream"
    }
    response = requests.put(url, headers=headers, data=updated_content)
    if response.status_code in [200, 201]:
        return response.json()  # returns file metadata after upload
    else:
        logging.error(f"Error updating file: {response.status_code} {response.text}")
        return None
    
# get user profile
def get_user_profile(access_token):
    url = "https://graph.microsoft.com/v1.0/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Error: {response.status_code} - {response.text}"}

#################################################################################
# App specific logic
#################################################################################

# handles initial login logic
def login():
    with app.app_context():
        # need access token to interact in any way with OneDrive API
        result = msal_app.acquire_token_interactive(SCOPES)

        if "access_token" in result:
            access_token = result.get("access_token")
            
            # sharing_url is stored in .env
            sharing_url = os.getenv("SHARED_FOLDER_URL")
            if not sharing_url:
                return "No shared folder URL provided in environment variables."

            # List the contents of the shared folder
            folder_items = list_shared_folder_contents(access_token, sharing_url)
            if folder_items is None:
                return "Failed to list folder contents."

            ###############################################################################################
            # TODO: replace this with logic for getting database
            target_filename = "test.txt"
            target_file = next((item for item in folder_items if item.get("name") == target_filename), None)
            if not target_file:
                return f"File '{target_filename}' not found in the shared folder."

            file_id = target_file.get("id")
            # Download the file
            file_content = download_file(access_token, file_id)
            if file_content is None:
                return "Failed to download the file."

            # ---- EDIT THE FILE CONTENT ----
            # Here, we assume the file is text-based. Adjust decoding/encoding as needed.
            try:
                text = file_content.decode("utf-8")
            except UnicodeDecodeError:
                return "Failed to decode file content."

            # For example, append a line of text.
            edited_text = text + "\nEdited on OneDrive via Graph API."

            # Convert back to bytes
            updated_content = edited_text.encode("utf-8")
            # ---- END EDITING ----

            # Reupload the file with the updated content
            update_result = update_file(access_token, file_id, updated_content)
            if update_result is None:
                return "Failed to update the file on OneDrive."
            ###############################################################################################

            
            user_data = get_user_profile(access_token)
            name = user_data.get("displayName", "Unknown User")
            
            return render_template("profile.html", file_id=file_id, name=name, update_result=update_result)
        else:
            return f"Login failed: {result.get('error_description', 'Unknown error')}"

#################################################################################
# Functions to initiate app
#################################################################################

# MSAL app setup
def _build_msal_app():
    return msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )

msal_app = _build_msal_app()

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
    flask_thread.daemon = True  # so that it exits when main thread exits
    flask_thread.start()
    
    start_webview()
