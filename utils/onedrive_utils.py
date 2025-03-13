import requests
import logging
import base64

# Uploads a file to a specified OneDrive folder, checking for duplicates.
def upload_new_file_no_duplicate(access_token, file_path, file_name, parent_folder_id):
    # Step 1: Check if file already exists in the folder
    check_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_folder_id}/children"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(check_url, headers=headers)
        if response.status_code != 200:
            return False, f"Error checking for existing files: {response.json()}"

        items = response.json().get("value", [])
        existing_file = next((item for item in items if item.get("name") == file_name), None)

        if existing_file:
            return False, "File with this name already exists."

        # Step 2: Upload the file if it does not exist
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_folder_id}:/{file_name}:/content"

        with open(file_path, "rb") as file:
            upload_response = requests.put(upload_url, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "text/plain"}, data=file)

        if upload_response.status_code in [200, 201]:  # 200 for overwrite, 201 for new file
            return True, "File uploaded successfully."
        else:
            return False, f"Error uploading file: {upload_response.json()}"

    except Exception as e:
        return False, f"Exception during upload: {e}"


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
        return [403]
    else:
        logging.error(f"Error listing folder contents: {response.status_code} {response.text}")
        return None

# download a file's content from OneDrive
def download_file_from_share_url(access_token, sharing_url):
    share_id = generate_share_id(sharing_url)
    # Using the /content endpoint returns the raw bytes of the file
    url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        logging.error(f"Error downloading file {sharing_url}: {response.status_code} {response.text}")
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
        logging.error(f"Error downloading file {file_id}: {response.status_code} {response.text}")
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

def update_file_from_share_url(access_token, sharing_url, updated_content):
    share_id = generate_share_id(sharing_url)  # Convert URL to share ID
    url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream"
    }

    response = requests.put(url, headers=headers, data=updated_content)

    if response.status_code in [200, 201]:
        try:
            return response.json()  # Return file metadata after update
        except ValueError:
            return {"message": "File updated successfully, but no JSON response."}
    else:
        logging.error(f"Error updating file {sharing_url}: {response.status_code} {response.text}")
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

