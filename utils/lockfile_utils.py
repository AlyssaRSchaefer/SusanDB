import requests
from flask import session
import os
from dotenv import load_dotenv
import base64

load_dotenv()

############################### LOCK FILE LOGIC ##################################################

SHARED_FOLDER_URL = os.getenv("SHARED_FOLDER_URL")  # The shared OneDrive folder URL
ONEDRIVE_API_BASE = "https://graph.microsoft.com/v1.0"
LOCK_FILE_NAME = "index.lock"  # Name of the lock file

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
    """Checks if the .lock file exists in the shared OneDrive folder."""
    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        return False  # Unable to retrieve folder info

    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]

    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children"
    response = requests.get(url, headers=get_onedrive_headers())

    if response.status_code == 200:
        items = response.json().get("value", [])
        return any(item["name"] == LOCK_FILE_NAME for item in items)  # Check if .lock file is in the folder
    
    return False  # Error fetching folder contents

def create_lock_file():
    """Creates a .lock file inside the shared OneDrive folder."""
    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        print("Error: Could not retrieve shared folder info.")
        return False  # Unable to retrieve folder info

    # NOTE: this system is needed to ensure it works for the user who owns the folder and the users who its shared with
    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]


    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children"

    file_metadata = {
        "name": LOCK_FILE_NAME,
        "file": {},  # This tells OneDrive it's a file, even though it's empty
        "@microsoft.graph.conflictBehavior": "replace"  # Replace existing lock file if it exists
    }

    response = requests.post(url, headers=get_onedrive_headers(), json=file_metadata)

    return response.status_code in [200, 201]  # Successfully created

def delete_lock_file(mode):
    """Deletes the .lock file from OneDrive only if no one is actively editing."""
    if mode == "view":
        print("in view mode, won't delete lock file")
        return False  # Don't delete if current user only has view permissions

    folder_info = get_shared_folder_drive_item()
    if not folder_info:
        return False  # Unable to retrieve folder info

    drive_id = folder_info["driveId"]
    item_id = folder_info["itemId"]

    url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{item_id}/children"
    response = requests.get(url, headers=get_onedrive_headers())

    if response.status_code == 200:
        items = response.json().get("value", [])
        lock_file = next((item for item in items if item["name"] == LOCK_FILE_NAME), None)

        if lock_file:
            print("found lock file, trying to delete!")
            lock_file_id = lock_file["id"]
            delete_url = f"{ONEDRIVE_API_BASE}/drives/{drive_id}/items/{lock_file_id}"
            delete_response = requests.delete(delete_url, headers=get_onedrive_headers())
            return delete_response.status_code in [200, 204]  # Successfully deleted

    return False  # Lock file not found or error