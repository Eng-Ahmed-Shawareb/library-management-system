"""
database.py
------------
Handles SQLite database creation, connection, and schema definition
for the Library Management System.
"""

import sqlite3
import os

DB_NAME = "library.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_connection():
    """Return a new SQLite connection with foreign keys enforced."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all tables if they do not already exist, and seed defaults."""
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- Books ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            publisher TEXT,
            publish_year INTEGER,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1,
            date_added TEXT NOT NULL
        )
    """)

    # ---------------- Members ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            address TEXT,
            membership_type TEXT NOT NULL DEFAULT 'Regular',
            max_books_allowed INTEGER NOT NULL DEFAULT 3,
            status TEXT NOT NULL DEFAULT 'Active',
            join_date TEXT NOT NULL
        )
    """)

    # ---------------- Loans ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            loan_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            fine_amount REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT
        )
    """)

    # ---------------- Librarians (login) ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS librarians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed a default admin account (username: admin / password: admin123)
    cur.execute("SELECT COUNT(*) AS c FROM librarians")
    if cur.fetchone()["c"] == 0:
        import hashlib
        default_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cur.execute(
            "INSERT INTO librarians (username, password_hash) VALUES (?, ?)",
            ("admin", default_hash),
        )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at: {DB_PATH}")
