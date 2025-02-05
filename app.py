from flask import Flask, g, render_template, jsonify, request
import sqlite3
import webview
import threading

app = Flask(__name__)
app.config["DATABASE"] = "students.db"

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
    # Here, you pass the dynamic variables to the template
    return render_template('auxiliary/layout.html', 
                           heading="Welcome to the Auxiliary Page", 
                           back_link="/")  # You can change this to any page you want

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
    if not sort:
        sort = {'name': 'ASC'}
    queried_data = query_db(sort)
    return jsonify(queried_data)

def get_field_order():
    with open("app/pref/field_order.txt", "r") as f:
        fields = [line.strip() for line in f.readlines()]
    return fields

def query_db(sort):
    db = get_db()
    field = list(sort.keys())[0]
    direction = sort[field]
    field_order = get_field_order()
    query = f"SELECT {', '.join(field_order)} FROM students ORDER BY {field} {direction};"
    students = db.execute(query).fetchall()
    result = [dict(row) for row in students]
    return result


# Main entry point
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window to load the Flask app
    webview.create_window('SusanDB', 'http://127.0.0.1:5000')
    webview.start()