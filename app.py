import os
import logging
from dotenv import load_dotenv
import msal
from flask import Flask, g, render_template, jsonify, request
import sqlite3
import webview
import threading
from flask import Flask, render_template, request, session, redirect, url_for
import requests
import base64
from io import BytesIO
import pandas as pd
import sys
import secrets
import tempfile

# Configure logging (optional)
# logging.basicConfig(level=logging.DEBUG)

# NOTE: TO USE THE ACCESS TOKEN OR STORE ANYTHING FOR THE SESSION (like an email) USE session["access_token"], etc.

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))
CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = os.getenv("AUTHORITY")
SCOPES = ["Files.ReadWrite.All", "Files.ReadWrite.AppFolder"]
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Should be msauth://redirect

if not all([CLIENT_ID, AUTHORITY, SCOPES, REDIRECT_URI]):
    raise ValueError("Missing required environment variables. Check your .env file.")

#################################################################################
# Generic functions for  retreiving/uploading to OneDrive
#################################################################################

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
# App specific and routing logic
#################################################################################


# handles initial login logic
@app.route('/login')
def login():
    with app.app_context():
        # need access token to interact in any way with OneDrive API
        result = msal_app.acquire_token_interactive(SCOPES)

        if "access_token" in result:
            session["access_token"] = result.get("access_token")

            user_data = get_user_profile(session["access_token"])
            name = user_data.get("displayName", "Unknown User")
            
            # sharing_url is stored in .env
            sharing_url = os.getenv("SHARED_FOLDER_URL")
            if not sharing_url:
                return "No shared folder URL provided in environment variables."

            # List the contents of the shared folder
            folder_items = list_shared_folder_contents(session["access_token"], sharing_url)
            if folder_items is None:
                return "Failed to list folder contents."
            
            session["folder_items"] = folder_items
            
            # i.e. access has been denied
            if folder_items[0] == 403:
                return render_template("login.html", name=name, access_denied=True)

            target_filename = "students.db"
            target_file = next((item for item in folder_items if item.get("name") == target_filename), None)
            if not target_file:
                return f"File '{target_filename}' not found in the shared folder."

            file_id = target_file.get("id")

            # Download the Excel file
            file_content = download_file(session["access_token"], file_id)
            if file_content is None:
                return "Failed to download the Excel file from OneDrive."
            
            try:
                # Save the database file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
                    temp_db.write(file_content)
                    temp_db_path = temp_db.name  # Store the file path
                
                # Open SQLite database
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()

                # Fetch student data
                cursor.execute("SELECT * FROM students")
                rows = cursor.fetchall()

                # Get column names
                columns = [desc[0] for desc in cursor.description]
                session["columns"] = columns

                # Convert to dictionary format
                student_data = [dict(zip(columns, row)) for row in rows]
                session["student_data"] = student_data

                # Close connection
                conn.close()
            except Exception as e:
                return f"Error reading database file: {e}"
            
            return render_template("database.html", name=name, students=student_data, field_order=columns)
        else:
            return f"Login failed: {result.get('error_description', 'Unknown error')}"

@app.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('index'))
        
# Define a route for the home page
app.config["DATABASE"] = "students.db"

@app.route('/')
def index():
    return redirect(url_for('templates'))
    #return render_template("login.html")

@app.route('/database')
def database():
    return render_template("database.html", students=session["student_data"], field_order=session["columns"])


@app.route('/import')
def import_data():
    return render_template('import.html')

@app.route('/templates')
def templates():
    templates = ['USER INFORMATION', 'TABLE 2', 'TABLE 3', 'TABLE 4']
    template = {
        'name': 'USER INFORMATION',
        'fields': [
            'First Name',
            'Last Name',
            'Email',
            'Phone Number',
            'Address',
            'Date of Birth',
            'First Name',
            'Last Name',
            'Email',
            'Phone Number',
            'Address',
            'Date of Birth'
        ]
    }
    return render_template('templates.html', template=template, templates=templates)

@app.route('/new_template')
def new_template():
    columns=['id', 'name', 'age', 'grade', 'favorite_subject', 'email', 'gpa', 'extracurricular']
    return render_template('new_template.html', columns=columns)

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

def start_webview():
    webview.create_window('SusanDB', url="http://127.0.0.1:5000/")
    webview.start()

@app.route('/layout')
def layout():
    # Here, you pass the dynamic variables to the template
    return render_template('auxiliary/layout.html', 
                           heading="Welcome to the Auxiliary Page", 
                           back_link="/")  # You can change this to any page you want

# Function to start Flask in a separate thread
def start_flask():
    app.run(port=5000)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # Allows dict-like access
    return g.db

# Read the field order from the text file
def get_field_order():
    with open("app/pref/field_order.txt", "r") as f:
        fields = [line.strip() for line in f.readlines()]
    return fields

# Close DB connection after request
@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Route to get all students
@app.route("/students", methods=["GET"])
def get_students():
    db = get_db()
    cursor = db.execute("SELECT * FROM students")
    students = [dict(row) for row in cursor.fetchall()]
    return jsonify(students)

# Main entry point
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True  # so that it exits when main thread exits
    flask_thread.start()
    
    start_webview()