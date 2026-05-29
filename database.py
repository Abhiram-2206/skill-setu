import sqlite3

DB_NAME = "database.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Existing skill-analysis tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skills TEXT,
        role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        learning_path TEXT,
        timeline TEXT,
        courses TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # Auth accounts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT    NOT NULL,
        email    TEXT    UNIQUE NOT NULL,
        password_hash TEXT,
        provider TEXT    NOT NULL DEFAULT 'local',
        provider_id   TEXT,
        avatar_url    TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
