import logging
import sqlite3
from contextlib import contextmanager

# Create a database connection
def create_connection():
    try:
        conn = sqlite3.connect('course_bot.db')
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None

# Context manager for database connection
@contextmanager
def get_db_connection():
    conn = create_connection()
    try:
        yield conn
    finally:
        if conn:
            conn.close()

# Initialize database tables
def init_db():
    create_users_table_query = '''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        tariff TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    
    create_feedback_table_query = '''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    '''
    
    create_module_progress_table_query = '''
    CREATE TABLE IF NOT EXISTS module_progress (
        user_id INTEGER,
        module_id INTEGER,
        completed BOOLEAN DEFAULT 0,
        completion_date TIMESTAMP,
        PRIMARY KEY (user_id, module_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    '''
    
    create_homework_submissions_table_query = '''
    CREATE TABLE IF NOT EXISTS homework_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        module_id INTEGER,
        submission TEXT,
        submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        feedback TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    '''
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_users_table_query)
            cursor.execute(create_feedback_table_query)
            cursor.execute(create_module_progress_table_query)
            cursor.execute(create_homework_submissions_table_query)
            conn.commit()
            logging.info("Database initialized successfully")
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")

# User-related database operations
def get_user(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Error getting user: {e}")
        return None

def add_user(user_id, username, first_name, last_name, tariff):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, tariff) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, first_name, last_name, tariff)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.error(f"Error adding user: {e}")
        return False

def update_user_tariff(user_id, tariff):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET tariff = ? WHERE user_id = ?",
                (tariff, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logging.error(f"Error updating user tariff: {e}")
        return False

# Feedback-related database operations
def add_feedback(user_id, message):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (user_id, message) VALUES (?, ?)",
                (user_id, message)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.error(f"Error adding feedback: {e}")
        return False

# Module progress database operations
def update_module_progress(user_id, module_id, completed=True):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if completed:
                cursor.execute(
                    "INSERT OR REPLACE INTO module_progress (user_id, module_id, completed, completion_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                    (user_id, module_id, completed)
                )
            else:
                cursor.execute(
                    "INSERT OR REPLACE INTO module_progress (user_id, module_id, completed, completion_date) VALUES (?, ?, ?, NULL)",
                    (user_id, module_id, completed)
                )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.error(f"Error updating module progress: {e}")
        return False

def get_module_progress(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT module_id, completed FROM module_progress WHERE user_id = ?",
                (user_id,)
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error getting module progress: {e}")
        return []

# Homework submission database operations
def add_homework_submission(user_id, module_id, submission):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO homework_submissions (user_id, module_id, submission) VALUES (?, ?, ?)",
                (user_id, module_id, submission)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logging.error(f"Error adding homework submission: {e}")
        return False

def get_homework_submissions(user_id, module_id=None):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if module_id:
                cursor.execute(
                    "SELECT * FROM homework_submissions WHERE user_id = ? AND module_id = ? ORDER BY submitted_date DESC",
                    (user_id, module_id)
                )
            else:
                cursor.execute(
                    "SELECT * FROM homework_submissions WHERE user_id = ? ORDER BY submitted_date DESC",
                    (user_id,)
                )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error getting homework submissions: {e}")
        return []

# Initialize the database on import
init_db()
