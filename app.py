from flask import Flask, g, session, render_template, jsonify, request
import os
from dotenv import load_dotenv
import msal
import sqlite3
import webview
import threading
from flask import Flask, render_template, request, session, redirect, url_for
import secrets
import tempfile
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from io import BytesIO
import re
from werkzeug.utils import secure_filename
import shutil 
import requests 

from onedrive_utils import get_user_profile, download_file_from_share_url, update_file_from_share_url

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
STUDENT_DB_URL=os.getenv("STUDENT_DB_URL")
REPORT_TEMPLATE_URL=os.getenv("REPORT_TEMPLATE_URL")

if not all([CLIENT_ID, AUTHORITY, SCOPES, REDIRECT_URI]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# running this at login will allow info to be stored in session so stuff does not have to constantly be reloaded
def run_at_login():
    user_data = get_user_profile(session["access_token"])
    session["name"] = user_data.get("displayName", "Unknown User")

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
            run_at_login()
            
            file_content = download_file_from_share_url(session["access_token"], STUDENT_DB_URL)

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

                columns = [desc[0] for desc in cursor.description]
                student_data = [dict(zip(columns, row)) for row in rows]

                conn.close()
            except Exception as e:
                return f"Error reading database file: {e}"
            
            return render_template("database.html", students=student_data, field_order=columns)
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
    # Download the Excel file
    file_content = download_file_from_share_url(session["access_token"], STUDENT_DB_URL)
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
    return render_template("database.html", students=student_data, field_order=columns)


@app.route('/import')
def import_data():
    return render_template('import.html')

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    if 'excel_file' not in request.files:
        return "No file part", 400
    file = request.files['excel_file']
    if file.filename == '':
        return "No selected file", 400

    if file and allowed_file(file.filename):
        #handle file saving and processing
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return "File uploaded", 200
    return "Invalid file type", 400

def upload_file_to_share_url(access_token, file_path, upload_url):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    with open(file_path, 'rb') as file_data:
        response = requests.put(upload_url, headers=headers, data=file_data)
    if response.status_code == 200:
        return {"message": "File uploaded successfully"}
    else:
        return {"error": f"Failed to upload file: {response.status_code}"}

@app.route('/delete-student', methods=['POST'])
def delete_student():
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify({"error": "Invalid student ID"}), 400

    # Download database file
    file_content = download_file_from_share_url(session.get("access_token"), STUDENT_DB_URL)

    if file_content is None:
        return jsonify({"error": "Failed to download database (file content is None)"}), 500

    print("File size:", len(file_content))  # Debug: check if data is actually downloaded

    # Save and verify content
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        temp_db.write(file_content)
        temp_db_path = temp_db.name  

    print("Database file saved to:", temp_db_path)

    # Try opening the database
    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Verify database integrity
        cursor.execute("PRAGMA integrity_check;")
        check_result = cursor.fetchone()
        print("PRAGMA integrity_check result:", check_result)

        cursor.execute("SELECT COUNT(*) FROM students;")
        student_count = cursor.fetchone()
        print("Number of students in DB before deletion:", student_count)

        # Ensure student ID is an integer
        print(f"Received student ID: {student_id}, type: {type(student_id)}")
        student_id = int(student_id)

        # Check if student exists
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        result = cursor.fetchone()
        
        if result is None:
            print(f"Student ID {student_id} not found in database.")  # Debugging line
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        else:
            print(f"Found student: {result}")  # Debugging line

        # Delete student
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        print("Database file modified time:", os.path.getmtime(temp_db_path))

        # Verify deletion
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        after_delete = cursor.fetchone()

        if after_delete is None:
            print(f"Student ID {student_id} successfully deleted.")
        else:
            print(f"ERROR: Student ID {student_id} still exists after deletion!")

        # Check student count after deletion
        cursor.execute("SELECT COUNT(*) FROM students;")
        student_count_after = cursor.fetchone()
        print("Number of students in DB after deletion:", student_count_after)

        conn.close()

        # Upload the modified database back to OneDrive (if needed)
        upload_response = upload_file_to_share_url(session.get("access_token"), temp_db_path, STUDENT_DB_URL)
        if "error" in upload_response:
            return jsonify(upload_response), 500

        print("Successfully uploaded the modified file to OneDrive.")
        return jsonify({"message": "Student deleted successfully"}), 200

    except Exception as e:
        print("Error opening or modifying database:", e)
        return jsonify({"error": f"Database error: {e}"}), 500

"""
@app.route('/delete-student', methods=['POST']) 
def delete_student():
    data = request.get_json()
    student_id = data.get('id')

    if not student_id:
        return jsonify({"error": "Invalid student ID"}), 400

    # Download database file
    file_content = download_file_from_share_url(session.get("access_token"), STUDENT_DB_URL)

    if file_content is None:
        return jsonify({"error": "Failed to download database (file content is None)"}), 500

    print("File size:", len(file_content))  # Debug: check if data is actually downloaded

    # Save and verify content
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        temp_db.write(file_content)
        temp_db_path = temp_db.name  

    print("Database file saved to:", temp_db_path)

    # Try opening the database
    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Verify database integrity
        cursor.execute("PRAGMA integrity_check;")
        check_result = cursor.fetchone()
        print("PRAGMA integrity_check result:", check_result)

        cursor.execute("SELECT COUNT(*) FROM students;")
        student_count = cursor.fetchone()
        print("Number of students in DB before deletion:", student_count)

        # Ensure student ID is an integer
        print(f"Received student ID: {student_id}, type: {type(student_id)}")
        student_id = int(student_id)

        # Check if student exists
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        result = cursor.fetchone()
        
        if result is None:
            print(f"Student ID {student_id} not found in database.")  # Debugging line
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        else:
            print(f"Found student: {result}")  # Debugging line

        # Delete student
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        print("Database file modified time:", os.path.getmtime(temp_db_path))
        # Verify deletion
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        after_delete = cursor.fetchone()

        if after_delete is None:
            print(f"Student ID {student_id} successfully deleted.")
        else:
            print(f"ERROR: Student ID {student_id} still exists after deletion!")

        # Check student count after deletion
        cursor.execute("SELECT COUNT(*) FROM students;")
        student_count_after = cursor.fetchone()
        print("Number of students in DB after deletion:", student_count_after)

        conn.close()
        return jsonify({"message": "Student deleted successfully"}), 200

    except Exception as e:
        print("Error opening or modifying database:", e)
        return jsonify({"error": f"Database error: {e}"}), 500
"""


@app.route('/get-student-files', methods=['POST'])
def get_student_files():
    data = request.get_json()
    student_id = data.get('id')
    
    if student_id:
        # Fetch associated files from database or storage
        files = [{"id": 1, "name": "File1.xlsx"}, {"id": 2, "name": "File2.pdf"}]  # Replace with actual file fetching
        return jsonify(files), 200
    return "Invalid student ID", 400



"""
def get_templates():
    templates_dict = {}

    # Download the Excel file from OneDrive
    file_content = download_file_from_share_url(session["access_token"], REPORT_TEMPLATE_URL)
    if not file_content:
        return "Failed to download the existing Excel file.", 500

    # Load the existing Excel file into memory
    excel_file = BytesIO(file_content)
    wb = load_workbook(excel_file)
    ws = wb.active

    # Loop through the rows in the Excel file and extract template fields
    for row in ws.iter_rows(min_row=2):  # Skip the header row
        template_name = row[0].value.upper()  # Assuming the template name is in the first column (A)
        fields = [cell.value.upper() for cell in row[1:] if cell.value]  # Extract subsequent columns (B, C, etc.)

        if template_name and fields:
            templates_dict[template_name] = fields
    
    return templates_dict

def get_all_fields():
    all_fields=['id', 'name', 'age', 'grade', 'favorite_subject', 'email', 'gpa', 'extracurricular']
    return all_fields
"""
@app.route('/generate_report')
def generate_report():
    #TODO: LOAD IN DYNAMICALLY
    all_fields = get_all_fields()
    templates_dict = get_templates()

    return render_template('auxiliary/generate_report.html', back_link="/database", templates=templates_dict, all_fields=all_fields)

@app.route('/templates')
def templates():
    #TODO: LOAD IN DYNAMICALLY
    all_fields = get_all_fields()
    templates_dict = get_templates()
    
    # Pass the dictionary to the template
    return render_template('templates.html', templates_dict=templates_dict, all_fields = all_fields)

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

        # Download the current Excel file from OneDrive
        file_content = download_file_from_share_url(session["access_token"], REPORT_TEMPLATE_URL)
        if not file_content:
            return {"error": "Failed to download the existing Excel file."}, 500

        # Load the existing Excel file into memory
        excel_file = BytesIO(file_content)
        wb = load_workbook(excel_file)
        ws = wb.active

        # Find the next available row for appending the data
        next_row = ws.max_row + 1

        # First column will be the template name
        ws[f"A{next_row}"] = template_name

        # Populate the selected columns in the subsequent columns
        for i, column in enumerate(selected_columns, start=2):  # Start at column B
            ws[f"{get_column_letter(i)}{next_row}"] = column

        # Save the workbook back to memory
        excel_file_output = BytesIO()
        wb.save(excel_file_output)
        excel_file_output.seek(0)

        # Upload the modified Excel file back to OneDrive
        upload_success = update_file_from_share_url(
            access_token, REPORT_TEMPLATE_URL, excel_file_output)

        if upload_success:
            return {"message": "Template appended successfully."}, 201
        else:
            return {"error": "Error, please try again"}, 500

# Normalize function: convert to lowercase and replace spaces with underscores
def normalize_name(name):
    return re.sub(r"\s+", "_", name.lower()) if name else None

@app.route('/api/update_template', methods=['POST'])
def update_template_api():
    data = request.json
    template_name = data.get("name")  # Template name to update
    updated_columns = data.get("columns")  # New column order

    if not template_name or not updated_columns:
        return {"error": "Template name and updated columns are required."}, 400

    access_token = session.get("access_token")
    if not access_token:
        return {"error": "User not authenticated. Please log in."}, 401

    # Download the current Excel file from OneDrive
    file_content = download_file_from_share_url(session["access_token"], REPORT_TEMPLATE_URL)
    if not file_content:
        return {"error": "Failed to download the existing Excel file."}, 500

    # Load the Excel file into memory
    excel_file = BytesIO(file_content)
    wb = load_workbook(excel_file)
    ws = wb.active

    # Find the row with the given template name
    template_row = None
    normalized_template_name = normalize_name(template_name)

    for row in range(2, ws.max_row + 1):  # Skip header row
        cell_value = normalize_name(ws[f"A{row}"].value)
        if cell_value == normalized_template_name:
            template_row = row
            break

    if not template_row:
        return {"error": "Template not found in the Excel file."}, 404

    # Clear the entire row (except template name in column A)
    for col in range(2, ws.max_column + 1):  # Start from column B
        ws[f"{get_column_letter(col)}{template_row}"] = None

    # Insert new attributes in the cleared row
    for i, column in enumerate(updated_columns, start=2):  # Start at column B
        ws[f"{get_column_letter(i)}{template_row}"] = column

    # Save the updated workbook back to memory
    excel_file_output = BytesIO()
    wb.save(excel_file_output)
    excel_file_output.seek(0)

    # Upload the modified Excel file back to OneDrive
    upload_success = update_file_from_share_url(access_token, REPORT_TEMPLATE_URL, excel_file_output)

    if upload_success:
        return {"message": "Template updated successfully."}, 200
    else:
        return {"error": "Error updating the template. Please try again."}, 500

@app.route('/api/delete_template', methods=['POST'])
def delete_template_api():
    data = request.json
    template_name = data.get("name")  # Template name to delete

    if not template_name:
        return {"error": "Template name is required."}, 400

    access_token = session.get("access_token")
    if not access_token:
        return {"error": "User not authenticated. Please log in."}, 401

    # Download the current Excel file from OneDrive
    file_content = download_file_from_share_url(session["access_token"], REPORT_TEMPLATE_URL)
    if not file_content:
        return {"error": "Failed to download the existing Excel file."}, 500

    # Load the Excel file into memory
    excel_file = BytesIO(file_content)
    wb = load_workbook(excel_file)
    ws = wb.active

    # Find the row with the given template name
    template_row = None
    normalized_template_name = normalize_name(template_name)

    for row in range(2, ws.max_row + 1):  # Skip header row
        cell_value = normalize_name(ws[f"A{row}"].value)
        if cell_value == normalized_template_name:
            template_row = row
            break

    if not template_row:
        return {"error": "Template not found in the Excel file."}, 404

    # Delete the entire row with the template (shift everything up)
    ws.delete_rows(template_row)

    # Save the updated workbook back to memory
    excel_file_output = BytesIO()
    wb.save(excel_file_output)
    excel_file_output.seek(0)

    # Upload the modified Excel file back to OneDrive
    upload_success = update_file_from_share_url(access_token, REPORT_TEMPLATE_URL, excel_file_output)

    if upload_success:
        return {"message": "Template deleted successfully."}, 200
    else:
        return {"error": "Error deleting the template. Please try again."}, 500



# Example API endpoint
@app.route('/api/greet', methods=['POST'])
def greet():
    data = request.json
    name = data.get('name', 'Guest')  # Default to 'Guest' if no name provided
    return jsonify(message=f"Hello, {name}!")

@app.route('/layout')
def layout():
    return render_template('auxiliary/layout.html', 
                           heading="Layout", 
                           back_link="/database")

"""
@app.route('/details<int:student_id>')
def details(student_id):
    print(f"Received student_id: {student_id}")
    selected_students = session.get('selected_students', [])
    students = get_students_by_ids(selected_students)
    print(f"Student: {students}") 
    return render_template('auxiliary/details.html',
                           heading=students[0]["name"],  #Assuming only one student
                           back_link="/database",
                           student=students)
"""  
@app.route('/details/<int:student_id>')
def details(student_id):
    print(f"Received student_id: {student_id}")
    students = get_students_by_ids([student_id])  #fetch student by ID
    if not students:
        return "Student not found", 404
    return render_template('auxiliary/details.html',
                           heading=students[0]["name"],
                           back_link="/database",
                           student=students[0])  #pass only the first student

@app.route('/generate-report')
def generate_report2():
    selected_students = session.get('selected_students', [])
    students = get_students_by_ids(selected_students)
    return render_template('auxiliary/generate-report.html',
                            heading = "Generate Report",
                            back_link="/database",
                            students = students)

@app.route('/store-selected-students', methods=['POST'])
def store_selected_students():
    data = request.json
    selected_students = data.get('selectedStudents', [])
    
    # Store selected students in the session
    session['selected_students'] = selected_students

    return jsonify({"message": "Selected students stored in session"}), 200

# Function to start Flask in a separate thread
def start_flask():
    app.run(port=5000, debug=False)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # Allows dict-like access
    return g.db

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

# DATABASE LOGIC
@app.route('/get_fields', methods=['GET'])
def get_fields():
    field_order = get_field_order()
    return jsonify(field_order)

@app.route('/get_data', methods=['POST'])
def get_data():
    data = request.json
    sort = data.get('sort', {})
    filter = data.get('filter', [])
    search = data.get('search', '')
    queried_data = query_db(sort, filter, search)
    return jsonify(queried_data)

def get_field_order():
    with open("app/pref/field_order.txt", "r") as f:
        fields = [line.strip() for line in f.readlines()]
    return fields

def query_db(sort, filter_params, search_term):
    db = get_db()
    field_order = get_field_order()

    # Construct ORDER BY clause
    order_by_clauses = [f"{field} {direction}" for field, direction in sort.items()]
    order_by_sql = ", ".join(order_by_clauses) if order_by_clauses else "id ASC"

    # Process filter parameters
    filters = []
    values = []
    for param in filter_params:
        field, value = param.split("-")  # Assuming format is "field-value"
        filters.append(f"{field} = ?")
        values.append(value)

    # Add search term filter
    if search_term:
        search_filter = " OR ".join([f"{field} LIKE ?" for field in field_order])  # Match search term against multiple fields
        filters.append(f"({search_filter})")
        values.extend([f"%{search_term}%" for _ in field_order])  # Add the search term with wildcards for LIKE clause

    where_clause = " AND ".join(filters) if filters else "1=1"  # Ensure valid WHERE clause

    # Construct the query
    query = f"SELECT {', '.join(field_order)}, id FROM students WHERE {where_clause} ORDER BY {order_by_sql};"

    students = db.execute(query, values).fetchall()
    result = [dict(row) for row in students]
    return result

@app.route('/get_student_fields', methods=['GET'])
def get_student_fields():
    db = get_db()
    cursor = db.execute("PRAGMA table_info(students);")
    fields = [row[1] for row in cursor.fetchall()]
    return jsonify(fields)

@app.route('/get_field_values', methods=['POST'])
def get_field_values():
    data = request.json
    field = data.get('field')
    db = get_db()
    query = f"SELECT DISTINCT {field} FROM students;"
    cursor = db.execute(query)
    values = [row[0] for row in cursor.fetchall()]  # Extract values
    return jsonify(values)

def get_students_by_ids(ids):
    db = get_db()
    placeholders = ",".join("?" for _ in ids)
    query = f"SELECT * FROM students WHERE id IN ({placeholders})"
    cursor = db.execute(query, ids)
    students = [dict(row) for row in cursor.fetchall()]
    return students

# MSAL app setup
def _build_msal_app():
    return msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )

msal_app = _build_msal_app()

# Main entry point
if __name__ == '__main__':
    """
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window to load the Flask app
    webview.create_window('SusanDB', 'http://127.0.0.1:5000')
    webview.start()
    """
    app.run(port=5000, debug=True)