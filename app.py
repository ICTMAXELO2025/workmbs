from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2 import sql
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database configuration - using environment variables for production
def get_db_config():
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'applications_wil'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'Maxelo@2023'),
        'port': os.environ.get('DB_PORT', '5432')
    }

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**get_db_config())
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def init_database():
    """Initialize the database and create messages table if it doesn't exist"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Create messages table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    surname VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        message = request.form['message']
        
        # Basic validation
        if not all([name, surname, email, message]):
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
        # Insert into database
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO messages (name, surname, email, message) VALUES (%s, %s, %s, %s)',
                    (name, surname, email, message)
                )
                conn.commit()
                cur.close()
                conn.close()
                flash('Message sent successfully!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Error sending message: {str(e)}', 'error')
                return redirect(url_for('index'))
        else:
            flash('Database connection error!', 'error')
            return redirect(url_for('index'))

@app.route('/messages')
def view_messages():
    """Route to view all messages (for admin purposes)"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM messages ORDER BY created_at DESC')
            messages = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('messages.html', messages=messages)
        except Exception as e:
            return f"Error retrieving messages: {str(e)}"
    else:
        return "Database connection error"

# Health check route for Render
@app.route('/health')
def health_check():
    return 'OK'

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)