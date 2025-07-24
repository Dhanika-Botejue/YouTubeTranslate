# init_db.py
import sqlite3

# Connect to SQLite database (will be created if it doesn't exist)
connection = sqlite3.connect("app.db")
cursor = connection.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Create videos table
cursor.execute("""
CREATE TABLE IF NOT EXISTS video (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_dst TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")

# Commit changes and close connection
connection.commit()
connection.close()

print("Database initialized successfully!")