import os, sqlite3
from flask import Flask, render_template, request, redirect,flash, url_for, session
from flask_session import Session
from datetime import datetime, timedelta
from functools import wraps



# initilize the Flask application
app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY")


def get_db_connection():
    try:
        conn = sqlite3.connect('library.db')
        conn.row_factory = sqlite3.Row  # Enables accessing rows like dictionaries
        return conn
    except sqlite3.Error as e:
        return None

def is_delete(user_id):
    # Mark user as deleted by setting the is_delete column to 1
    try:
        # get the db connection
        conn = get_db_connection()
        c = conn.cursor()
        
        # Update the user's is_delete column
        c.execute("UPDATE users SET is_delete = 1 WHERE id=?", (user_id,))
        
        # commit the changes
        conn.commit()
        
        # close the connection
        conn.close()
        # if successful
        return True
    except Exception as e:
         # Error message
        print(f"Error deleting user: {e}") 
        # if something goes wrong
        return False
    
    # check if the admin exists 
def admin_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admin WHERE is_active = 1")
    admin_count = cursor.fetchone()[0]  # This will always return a number (0 or more)
    conn.close()
    return admin_count > 0  # Returns True if at least one active admin exists

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Decorator triggered")
        print("Session data:", session)
        if session.get("admin_id") is None:
            print("Redirecting to login...")
            session.clear()  # Ensure session is cleared
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

    
        
    
                     
    
  
    
    





















