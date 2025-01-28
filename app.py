from flask import Flask, render_template, jsonify, request
import webview
import threading

# Initialize Flask app
app = Flask(__name__)

# Define a route for the home page
@app.route('/')
def index():
    return render_template('database.html')

@app.route('/database')
def database():
    return render_template('database.html')

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

# Main entry point
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create a PyWebView window to load the Flask app
    webview.create_window('Flask + PyWebView', 'http://127.0.0.1:5000')
    webview.start()
