from flask import Flask, g, render_template, jsonify, request
import sqlite3
import webview
import threading

app = Flask(__name__)
app.config["DATABASE"] = "students.db"

@app.route('/')
def index():
    return render_template('database.html')

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

# Function to start Flask in a separate thread
def start_flask():
    app.run(port=5000, debug=False)

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
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window to load the Flask app
    webview.create_window('SusanDB', 'http://127.0.0.1:5000')
    webview.start()
