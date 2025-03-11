import requests
from flask import session
import os
from dotenv import load_dotenv
import base64
import time

load_dotenv()

############################### LOCK FILE LOGIC ##################################################

SHARED_FOLDER_URL = os.getenv("SHARED_FOLDER_URL")  # The shared OneDrive folder URL
ONEDRIVE_API_BASE = "https://graph.microsoft.com/v1.0"
LOCK_FILE_NAME = "index.lock"  # Name of the lock file
LOCK_FILE_TIMEOUT = 20   # 15 minutes

def get_onedrive_headers():
    """Returns headers for authenticated OneDrive API requests."""
    access_token = session.get("access_token")
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

def generate_share_id(shared_url):
    """Generates the share ID from the shared URL."""
    encoded_url = base64.urlsafe_b64encode(shared_url.encode('utf-8')).rstrip(b'=').decode('utf-8')
    return f"u!{encoded_url}"

def get_shared_folder_drive_item():
    """Retrieves the DriveItem ID and driveId of the shared folder."""
    share_id = generate_share_id(SHARED_FOLDER_URL)
    url = f"{ONEDRIVE_API_BASE}/shares/{share_id}/driveItem"

    response = requests.get(url, headers=get_onedrive_headers())

    if response.status_code == 200:
        data = response.json()
        return {"driveId": data["parentReference"]["driveId"], "itemId": data["id"]}
    else:
        print(f"Error retrieving shared folder info: {response.status_code} - {response.text}")
        return None

def check_lock_file():
    """Checks if the lock file exists and if it's expired (>15 mins old). Returns (timestamp, username) or False if not valid."""
    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        return False  

    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]

    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children/{LOCK_FILE_NAME}/content"
    response = requests.get(url, headers=get_onedrive_headers())

    if response.status_code == 200:
        content_lines = response.text.strip().split("\n")


        lock_timestamp = int(content_lines[0])  # First line = timestamp
        lock_user = content_lines[1]  # Second line = username

        current_time = int(time.time())

        if current_time - lock_timestamp > LOCK_FILE_TIMEOUT:
            print(f"Lock expired (User: {lock_user}), deleting...")
            delete_lock_file(None)
            return False  # Lock expired and deleted

        print(f"Lock is active (User: {lock_user}, Timestamp: {lock_timestamp})")
        return lock_timestamp, lock_user  # Lock is still valid

    return False  # Lock file does not exist


def create_lock_file():
    """Creates a .lock file with a timestamp inside the shared OneDrive folder."""
    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        print("Error: Could not retrieve shared folder info.")
        return False  

    # NOTE: this system is needed to ensure it works for the user who owns the folder and the users who its shared with
    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]
    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children"

    timestamp = int(time.time())  # Current UNIX timestamp
    user_name = session.get("name", "Unknown User")  # Retrieve user name from session

    file_content = f"{timestamp}\n{user_name}"  # Store timestamp on the first line, username on the second

    response = requests.put(
        f"{url}/{LOCK_FILE_NAME}/content",
        headers=get_onedrive_headers(),
        data=file_content
    )

    return response.status_code in [200, 201]

def update_lock_timestamp():
    """Updates the timestamp while keeping the same username inside the lock file."""
    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        return  

    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]

    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children/{LOCK_FILE_NAME}/content"

    existing_user_name = session.get("name", "Unknown User")  # Default to session user

    new_timestamp = str(int(time.time()))

    new_file_content = f"{new_timestamp}\n{existing_user_name}"  # Keep username, update timestamp

    requests.put(url, headers=get_onedrive_headers(), data=new_file_content)

def delete_lock_file(mode):
    """Deletes the .lock file from OneDrive."""
    if mode == "view":
        print("in view mode, won't delete lock file")
        return False  # Don't delete if current user only has view permissions
    
    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        return False  

    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]

    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children/{LOCK_FILE_NAME}"
    response = requests.delete(url, headers=get_onedrive_headers())

    return response.status_code in [200, 204]