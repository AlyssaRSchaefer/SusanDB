import sqlite3

DB_NAME = "instance/students.db"  # Store database inside the Flask instance folder

def create_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            grade INTEGER,
            favorite_subject TEXT,
            email TEXT UNIQUE,
            gpa REAL,
            extracurricular TEXT
        )
    ''')

    # Sample data
    students_data = [
        ("Emma Johnson", 16, 11, "Mathematics", "emma.johnson@example.com", 3.8, "Basketball"),
        ("Liam Smith", 15, 10, "Physics", "liam.smith@example.com", 3.6, "Debate Club"),
        ("Olivia Martinez", 17, 12, "Biology", "olivia.martinez@example.com", 4.0, "Science Olympiad"),
        ("Noah Brown", 16, 11, "Computer Science", "noah.brown@example.com", 3.9, "Coding Club"),
        ("Ava Davis", 15, 10, "History", "ava.davis@example.com", 3.7, "Drama Club")
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO students (name, age, grade, favorite_subject, email, gpa, extracurricular)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', students_data)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    create_db()