from flask import Flask, g, session, render_template, jsonify, request
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
from fpdf import FPDF
import os
import json


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
FIELDS_ORDER_URL = os.getenv("FIELDS_ORDER_URL")

STUDENT_DB_LOCAL_PATH="students_local.db"
FIELD_ORDER_LOCAL_PATH="field_order.txt"

if not all([CLIENT_ID, AUTHORITY, SCOPES, REDIRECT_URI]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# running this at login will allow info to be stored in session so stuff does not have to constantly be reloaded
def run_at_login():
    user_data = get_user_profile(session["access_token"])
    session["name"] = user_data.get("displayName", "Unknown User")
    session["id"] = user_data.get("id")
    session["color_scheme"] = get_color_scheme(session["id"])

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
            return render_template("database.html", delete_mode=False)
        else:
            return f"Login failed: {result.get('error_description', 'Unknown error')}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
        
@app.route('/')
def index():
    return render_template("login.html")

@app.route('/database')
def database():
    return render_template("database.html", delete_mode=False)

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/edit_database')
def edit_database():
    return render_template("auxiliary/edit_database.html", back_link="/database", heading="Edit Database")

@app.route('/import')
def import_data():
    return render_template('import.html')

@app.route('/add_field')
def add_field():
    return render_template('auxiliary/edit_database_action.html', back_link="/database", heading="Add New Field", mode="add_field")

@app.route('/delete_field')
def delete_field():
    return render_template('auxiliary/edit_database_action.html', back_link="/database", heading="Delete Field", mode="delete_field")

@app.route('/add_student')
def add_student():
    return render_template('auxiliary/edit_database_action.html', back_link="/database", heading="Add New Student", mode="add_student")

@app.route('/delete_student')
def delete_student():
    return render_template('database.html', delete_mode=True)

def get_color_scheme(id):
    if id is None:
        return "default"
    
    db = get_db()
    query = "SELECT color_scheme FROM user_settings WHERE id = ?"
    result = db.execute(query, (id,)).fetchone()

    if result:
        db.close()
        return result[0]
    
    # If ID is not found, insert a new row with a default color scheme
    insert_query = "INSERT INTO user_settings (id, color_scheme) VALUES (?, ?)"
    db.execute(insert_query, (id, "default"))
    db.commit()
    db.close()
    save_db()
    
    return "default"  # Return the default color scheme

@app.route('/get_color_scheme_session')
def get_color_scheme_session():
    color_scheme = session.get('color_scheme', 'default')
    return jsonify({'color_scheme': color_scheme})

@app.route("/update_color_scheme", methods=["POST"])
def update_color_scheme():
    
    if "id" not in session:
        return jsonify({"error": "User not logged in"}), 403  # Unauthorized

    user_id = session["id"]
    color_scheme = request.json.get("colorScheme")
    session["color_scheme"] = color_scheme

    db = get_db()
    cursor = db.cursor()

    # Check if the user already has a color scheme saved
    query = "SELECT 1 FROM user_settings WHERE id = ?"
    result = cursor.execute(query, (user_id,)).fetchone()

    if result:
        # Update existing entry
        update_query = "UPDATE user_settings SET color_scheme = ? WHERE id = ?"
        cursor.execute(update_query, (color_scheme, user_id))
    else:
        # Insert new entry
        insert_query = "INSERT INTO user_settings (id, color_scheme) VALUES (?, ?)"
        cursor.execute(insert_query, (user_id, color_scheme))

    db.commit()
    db.close()
    save_db()

    return jsonify({"message": "Color scheme updated successfully", "colorScheme": color_scheme})

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
    db = get_db()
    cursor = db.execute("PRAGMA table_info(students);")
    fields = [row[1] for row in cursor.fetchall()]
    fields.remove("id")
    return jsonify(fields)

@app.route('/generate_report', methods=['GET', 'POST'])
def generate_report():

    if request.method == 'GET':
        all_fields = json.loads(get_all_fields().data)
        templates_dict = get_templates()

        return render_template('auxiliary/generate_report.html', back_link="/database", templates=templates_dict, all_fields=all_fields)
    if request.method == 'POST':
        student_ids = request.args.getlist('ids[]')

        try:
            # Get JSON data from frontend
            data = request.json
            selected_fields = data.get("fields", [])

            print(student_ids)

            if not selected_fields:
                return jsonify({"success": False, "error": "No fields selected"}), 400
            
            student_data = get_students_by_ids(student_ids, selected_fields)

            # Generate PDF using PyWebView's file dialog
            pdf_path = generate_pdf(student_data, selected_fields)

            if not pdf_path:
                return jsonify({"success": False, "error": "User canceled save dialog"}), 400
            try:
                os.startfile(pdf_path)
            except:
                print("can't open it")

            return jsonify({
                "success": True,
                "message": "Report generated successfully",
                "report_path": pdf_path
            })

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

def generate_pdf(data, fields):
    """Generate a PDF report with individual student tables on separate pages using FPDF."""
    file_types = ('PDF (*.pdf)', 'All files (*.*)')
    file_path = webview.windows[0].create_file_dialog(
        webview.SAVE_DIALOG,
        file_types=file_types
    )

    if not file_path:
        return None
    if isinstance(file_path, list):
        file_path = file_path[0]

    # Create a PDF object
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Auto page break with margin
    pdf.set_margins(20, 15, 20)  # (left, top, right) margins

    for student in data:
        pdf.add_page()  # Add a new page for each student

        # Set font for the title
        pdf.set_font("Times", style="B", size=16)

        # Find the index where "name" appears in fields (case-insensitive)
        name_index = next((i for i, field in enumerate(fields) if "name" in field.lower()), None)

        if name_index is not None:  # If "name" is found in fields
            title = f"Student Report - {student[name_index]}"
        else:
            title = "Student Report"

        pdf.cell(0, 10, title, ln=True, align="C")  # Use the correct title
        pdf.ln(5)  # Add some space after the title

        # Set font for the table
        pdf.set_font("Times", size=12)

        # Create a table for the student's data
        for field, value in zip(fields, student):
            # Add field name in bold
            pdf.set_font("Times", style="B", size=12)
            pdf.cell(60, 10, field, border=1)

            # Add value with text wrapping
            pdf.set_font("Times", size=12)
            pdf.multi_cell(0, 10, str(value), border=1)
            pdf.ln(0)  # Reset line break after multi_cell

        pdf.ln(10)  # Add some space between students

    # Save the PDF
    pdf.output(file_path)
    return file_path


@app.route('/templates')
def templates():
    all_fields = json.loads(get_all_fields().data)
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

@app.route('/layout')
def layout():
    return render_template('auxiliary/layout.html', 
                           heading="", 
                           back_link="/database")

@app.route('/details')
def details():
    return render_template('auxiliary/details.html',
                           heading="test",  # Assuming only one student
                           back_link="/database")

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
        # Check if local copy exists, otherwise download
        if not os.path.exists(STUDENT_DB_LOCAL_PATH):
            download_and_store_file(STUDENT_DB_LOCAL_PATH, STUDENT_DB_URL)
        g.db = sqlite3.connect(STUDENT_DB_LOCAL_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def save_db():
    upload_file_to_onedrive(STUDENT_DB_LOCAL_PATH, STUDENT_DB_URL)

def get_field_order():
    # Check if local copy exists, otherwise download
    if not os.path.exists(FIELD_ORDER_LOCAL_PATH):
        download_and_store_file(FIELD_ORDER_LOCAL_PATH, FIELDS_ORDER_URL)
    
    try:
        with open(FIELD_ORDER_LOCAL_PATH, "r", encoding="utf-8") as f:
            field_order = f.read().strip().split("\n")
        return [field.strip() for field in field_order if field.strip()]
    except Exception as e:
        print(f"Error reading field order file: {e}")
        return None

# This function downloads a local copy of a OneDrive file at a given path
def download_and_store_file(local_path, url):
    """Download a file from OneDrive and store it locally."""
    file_content = download_file_from_share_url(session["access_token"], url)
    
    if file_content is None:
        raise Exception(f"Failed to download file from OneDrive: {url}")
    
    # Save the file locally
    with open(local_path, "wb") as f:
        f.write(file_content)

# This function uploads a local file to a OneDrive url
def upload_file_to_onedrive(local_path, url):
    """Upload a local file back to OneDrive."""
    with open(local_path, "rb") as f:
        file_content = f.read()
    
    success = update_file_from_share_url(session["access_token"], url, file_content)
    
    if not success:
        raise Exception(f"Failed to upload file to OneDrive: {url}")

@app.teardown_appcontext
def close_db(exception):
    """Close database connection at the end of request."""
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

@app.route('/save_fields', methods=['POST'])
def save_fields():
    """Save the updated field order and upload it back to OneDrive."""
    try:
        data = request.get_json()
        new_field_order = data.get("fields")

        if not isinstance(new_field_order, list):
            return jsonify({"error": "Invalid data format. Expected a list."}), 400

        # Write the new field order to the local file
        with open(FIELD_ORDER_LOCAL_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(new_field_order))

        # Upload the updated file back to OneDrive
        upload_file_to_onedrive(FIELD_ORDER_LOCAL_PATH, FIELDS_ORDER_URL)

        return jsonify({"message": "Field order successfully updated."}), 200

    except Exception as e:
        print(f"Error saving field order: {e}")
        return jsonify({"error": "Failed to save field order."}), 500


@app.route('/get_data', methods=['POST'])
def get_data():
    data = request.json
    sort = data.get('sort', {})
    filter = data.get('filter', [])
    search = data.get('search', '')
    queried_data = query_db(sort, filter, search)
    return jsonify(queried_data)

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
    return get_all_fields()

@app.route('/get_field_values', methods=['POST'])
def get_field_values():
    data = request.json
    field = data.get('field')
    db = get_db()
    query = f"SELECT DISTINCT {field} FROM students;"
    cursor = db.execute(query)
    values = [row[0] for row in cursor.fetchall()]  # Extract values
    return jsonify(values)

@app.route('/add_field_to_db', methods=['POST'])
def add_field_to_db():
    data = request.json
    field = data.get('field')
    default_value = data.get('default')
    add_to_layout = data.get('addToLayout')

    db = get_db()
    query = f"ALTER TABLE students ADD COLUMN \"{field}\" TEXT DEFAULT '{default_value}'"
    db.execute(query)
    db.commit()
    db.close()
    save_db()

    if add_to_layout:
        try:
            # Ensure we have the latest field order file
            if not os.path.exists(FIELD_ORDER_LOCAL_PATH):
                download_and_store_file(FIELD_ORDER_LOCAL_PATH, FIELDS_ORDER_URL)

            # Read existing field order
            with open(FIELD_ORDER_LOCAL_PATH, "r", encoding="utf-8") as f:
                field_order = f.read().strip().split("\n")

            # Append the new field if it's not already present
            if field not in field_order:
                field_order.append(field)

                # Write updated field order back to the file
                with open(FIELD_ORDER_LOCAL_PATH, "w", encoding="utf-8") as f:
                    f.write("\n".join(field_order))

                # Upload the updated field order back to OneDrive
                upload_file_to_onedrive(FIELD_ORDER_LOCAL_PATH, FIELDS_ORDER_URL)

        except Exception as e:
            return jsonify({"error": f"Failed to update field order: {str(e)}"}), 500

    return jsonify({"message": "Field added successfully."}), 200


@app.route('/delete_field_from_db', methods=['POST'])
def delete_field_from_db():
    data = request.json
    field = data.get('field')

    db = get_db()
    query = f"ALTER TABLE students DROP COLUMN \"{field}\""
    db.execute(query)
    db.commit()
    db.close()
    save_db()

    try:
        if not os.path.exists(FIELD_ORDER_LOCAL_PATH):
            download_and_store_file(FIELD_ORDER_LOCAL_PATH, FIELDS_ORDER_URL)

        with open(FIELD_ORDER_LOCAL_PATH, "r", encoding="utf-8") as f:
            field_order = f.read().strip().split("\n")

        if field in field_order:
            field_order.remove(field)

            with open(FIELD_ORDER_LOCAL_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(field_order))

            upload_file_to_onedrive(FIELD_ORDER_LOCAL_PATH, FIELDS_ORDER_URL)

    except Exception as e:
        return jsonify({"error": f"Failed to update field order: {str(e)}"}), 500

    return jsonify({"message": "Field deleted successfully."}), 200

@app.route('/add_student_to_db', methods=['POST'])
def add_student_to_db():
    data = request.form.to_dict()  # Extract form data as a dictionary

    if not data:
        return jsonify({"error": "No data received"}), 400

    db = get_db()
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    query = f"INSERT INTO students ({columns}) VALUES ({placeholders})"
    
    try:
        db.execute(query, tuple(data.values()))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

    save_db()
    return render_template('auxiliary/edit_database_action.html', back_link="/database", heading="Student Added", mode="add_student_result")

@app.route('/delete_students_from_db', methods=['POST'])
def delete_students_from_db():
    data = request.json
    student_ids = data.get("ids")

    if not student_ids:
        return jsonify({"error": "No student IDs provided"}), 400

    db = get_db()
    
    try:
        # Create a placeholder for each student ID
        placeholders = ", ".join("?" for _ in student_ids)
        query = f"DELETE FROM students WHERE id IN ({placeholders})"
        
        db.execute(query, tuple(student_ids))  # Pass as tuple
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
    
    save_db()
    return jsonify({"message": "Students deleted successfully."}), 200

@app.route('/update_database_cell', methods=['POST'])
def update_database_cell():
    data = request.json
    id = data.get("id")
    field = data.get("field")
    new_value = data.get("newValue")

    db = get_db()
    try:
        # Create the query string dynamically
        query = f"UPDATE students SET {field} = ? WHERE id = ?"
        
        # Execute the query
        db.execute(query, (new_value, id))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
    
    save_db()
    return jsonify({"message": "Student data updated successfully."}), 200

@app.route('/get_student', methods=['POST'])
def get_student():
    data = request.get_json()
    student_id = data.get('id')
    if not student_id:
        return jsonify({"error": "No student ID provided"}), 400
    try:
        student = get_student_by_id(student_id)
        if student:
            return jsonify(student)
        else:
            return jsonify({"error": "Student not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_students_by_ids(ids, selected_fields):
    db = get_db()
    # Fetch student data for selected IDs and fields
    if not selected_fields:  # checks for an empty list
        fields_str = "*"
    else:
        fields_str = ", ".join(selected_fields)
    placeholders = ", ".join("?" for _ in ids)
    query = f"SELECT {fields_str} FROM students WHERE id IN ({placeholders})"
    cursor=db.execute(query, ids)
    student_data = cursor.fetchall()
    return student_data

def get_student_by_id(id):
    db = get_db()
    query = "SELECT * FROM students WHERE id = ?"
    cursor = db.execute(query, (id,))
    student = cursor.fetchone()
    db.close()
    if student:
        # Convert row to dictionary using cursor description
        columns = [col[0] for col in cursor.description]
        student_dict = dict(zip(columns, student))
        student_dict.pop('id', None)
        return student_dict
    return None

# MSAL app setup
def _build_msal_app():
    return msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )

msal_app = _build_msal_app()

# Main entry point
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window to load the Flask app
    webview.create_window('SusanDB', 'http://127.0.0.1:5000', fullscreen=True)
    webview.start()