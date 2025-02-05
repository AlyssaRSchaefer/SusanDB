import os
from dotenv import load_dotenv
import msal
from flask import Flask, g, render_template, jsonify, request
import sqlite3
import webview
import threading
from flask import Flask, render_template, request, session, redirect, url_for
import secrets
import tempfile

from onedrive_utils import upload_new_file_no_duplicate, generate_share_id, list_shared_folder_contents, download_file, update_file, get_user_profile

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

                # Convert to dictionary format
                student_data = [dict(zip(columns, row)) for row in rows]

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
    #return redirect(url_for('templates'))
    return render_template("login.html")

@app.route('/database')
def database():
    return render_template("database.html", students=session["student_data"], field_order=session["columns"])


@app.route('/import')
def import_data():
    return render_template('import.html')

@app.route('/templates')
def templates():
    # Get the access token from the session (assumes the user is logged in)
    access_token = session.get("access_token")
    
    # Ensure that the access token exists
    if not access_token:
        return "User is not logged in or session expired."

    # The shared folder URL (retrieved from environment variable or another method)
    shared_folder_url = os.getenv("SHARED_FOLDER_URL")
    
    # List the contents of the shared folder
    folder_items = list_shared_folder_contents(access_token, shared_folder_url)

    # Check if the shared folder contains a 'report_templates' folder
    report_templates_folder = None
    for item in folder_items:
        if item.get("name") == "report_templates" and item.get("folder"):
            report_templates_folder = item
            break

    if not report_templates_folder:
        return "report_templates folder not found in the shared OneDrive folder."

    # Now list the contents of the 'report_templates' folder
    folder_items = list_shared_folder_contents(access_token, report_templates_folder["webUrl"])

    templates_dict = {}

    # Loop through the files in the 'report_templates' folder
    for item in folder_items:
        if item.get("name").endswith('.txt') and item.get("file"):
            template_name = item.get("name").split('.')[0]  # Remove .txt extension
            file_id = item.get("id")

            # Download the file content (it will be the template fields)
            file_content = download_file(access_token, file_id)
            if not file_content:
                continue

            # Read the file content and split it into fields (each line)
            fields = file_content.decode('utf-8').splitlines()

            # Add the template name and its fields to the dictionary
            templates_dict[template_name] = fields

    # If no templates are found, return a message
    if not templates_dict:
        return "No templates found in the 'report_templates' folder."

    # Pass the dictionary to the template
    return render_template('templates.html', templates_dict=templates_dict)

@app.route('/new_template', methods=['GET', 'POST'])
def new_template():
    if request.method == 'GET':
        columns = ['id', 'name', 'age', 'grade', 'favorite_subject', 'email', 'gpa', 'extracurricular']
        return render_template('auxiliary/new_template.html', back_link="/templates", columns=columns)
    elif request.method == 'POST':
        # Get JSON data from request
        data = request.json
        template_name = data.get("name")
        selected_columns = data.get("columns")

        if not template_name or not selected_columns:
            return {"error": "Template name and columns are required."}, 400

        
        access_token = session.get("access_token")
        if not access_token:
            return {"error": "User not authenticated. Please log in."}, 401

        # Retrieve shared folder contents
        sharing_url = os.getenv("SHARED_FOLDER_URL")
        folder_items = list_shared_folder_contents(access_token, sharing_url)
        if not folder_items:
            return {"error": "Failed to retrieve shared folder contents."}, 500

        # Find "report_templates" folder
        report_templates_folder = next((item for item in folder_items if item.get("name") == "report_templates"), None)
        if not report_templates_folder:
            return {"error": "report_templates folder not found in OneDrive."}, 404

        report_templates_folder_id = report_templates_folder.get("id")
        # Create the template file content
        file_content = "\n".join(selected_columns)  # Each column in a new line

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(file_content.encode("utf-8"))
            temp_file_path = temp_file.name

        # Upload the file to OneDrive inside report_templates
        file_name = f"{template_name}.txt"
        upload_success = upload_new_file_no_duplicate(access_token, temp_file_path, file_name, report_templates_folder_id)

        # Remove temporary file
        os.remove(temp_file_path)

        if upload_success[0]:
            return {"message": "Template created successfully."}, 201
        else:
            return {"error": upload_success[1]}, 500

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