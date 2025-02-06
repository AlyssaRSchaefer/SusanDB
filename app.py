from flask import Flask, g, session, render_template, jsonify, request
import sqlite3
import webview
import threading

app = Flask(__name__)
app.config["DATABASE"] = "students.db"
app.secret_key = 'key'

@app.route('/')
def index():
    return render_template('auxiliary/layout.html', 
                           heading="Layout Heading", 
                           back_link="/database")

@app.route('/database')
def database():
    db = get_db()
    field_order = get_field_order()

    # Build dynamic SQL query
    sql_query = f"SELECT {', '.join(field_order)} FROM students"
    students = db.execute(sql_query).fetchall()

    return render_template("database.html", students=students, field_order=field_order)


@app.route('/import')
def import_data():
    return render_template('import.html')

@app.route('/templates')
def templates():
    return render_template('templates.html')


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

@app.route('/details')
def details():
    selected_students = session.get('selected_students', [])
    students = get_students_by_ids(selected_students)
    return render_template('auxiliary/details.html',
                           heading=students[0]["name"],  # Assuming only one student
                           back_link="/database",
                           student=students)

@app.route('/generate-report')
def generate_report():
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

    if not sort:
        sort = {'name': 'ASC'}
        
    queried_data = query_db(sort, filter)
    return jsonify(queried_data)

def get_field_order():
    with open("app/pref/field_order.txt", "r") as f:
        fields = [line.strip() for line in f.readlines()]
    return fields

def query_db(sort, filter_params):
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

    where_clause = " AND ".join(filters) if filters else "1=1"  # Ensure valid WHERE clause

    # Construct the query
    query = f"SELECT {', '.join(field_order)}, id FROM students WHERE {where_clause} ORDER BY {order_by_sql};"

    students = db.execute(query, values).fetchall()
    result = [dict(row) for row in students]
    return result

def get_students_by_ids(ids):
    db = get_db()
    placeholders = ",".join("?" for _ in ids)
    query = f"SELECT * FROM students WHERE id IN ({placeholders})"
    cursor = db.execute(query, ids)
    students = [dict(row) for row in cursor.fetchall()]
    return students


# Main entry point
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window to load the Flask app
    webview.create_window('SusanDB', 'http://127.0.0.1:5000')
    webview.start()