import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'notices.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Create notices table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            notice_date TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default admin user if not exists
    cur.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (
            'admin',
            generate_password_hash('admin123')
        ))
        print(" Created admin account -> username: admin, password: admin123")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
