import sqlite3
import random

DB_NAME = "instance/students.db"  # Store database inside the Flask instance folder

def create_db():
    conn = sqlite3.connect("students_local.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id TEXT PRIMARY KEY,
            color_scheme TEXT DEFAULT 'default'
        )
    """)

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
        ("Ava Davis", 15, 10, "History", "ava.davis@example.com", 3.7, "Drama Club"),
        ("Maura Davis", 14, 9, "History", "maura.davis@example.com", 3.7, "Drama Club")
    ]

    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Charles", "Thomas",
               "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Anderson", "Clark", "Rodriguez", "Lewis", "Walker", "Hall", "Allen", "Young", "Hernandez", "King"]
    subjects = ["Mathematics", "Physics", "Biology", "Chemistry", "History", "English", "Computer Science", "Music"]
    extracurriculars = ["Soccer", "Basketball", "Drama Club", "Debate Club", "Coding Club", "Chess Club", "Music Band", "Art Club"]

    def generate_email(name):
        return name.lower().replace(" ", ".") + "@example.com"

    for _ in range(50):
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first} {last}"
        age = random.randint(14, 18)
        grade = random.randint(9, 12)
        subject = random.choice(subjects)
        email = generate_email(name)
        gpa = round(random.uniform(2.5, 4.0), 2)
        activity = random.choice(extracurriculars)
        students_data.append((name, age, grade, subject, email, gpa, activity))

    cursor.executemany('''
        INSERT OR IGNORE INTO students (name, age, grade, favorite_subject, email, gpa, extracurricular)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', students_data)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    create_db()