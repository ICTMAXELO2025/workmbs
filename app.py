from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

# Database configuration
def get_db_connection():
    """Create and return a database connection"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Use the connection string provided by Render
            logger.info(f"Using DATABASE_URL: {database_url[:20]}...")
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            conn = psycopg2.connect(database_url)
            logger.info("Database connection successful using DATABASE_URL")
        else:
            # Fallback to individual parameters
            logger.info("Using individual database parameters")
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'applications_wil'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'Maxelo@2023'),
                port=os.environ.get('DB_PORT', '5432')
            )
            logger.info("Database connection successful using individual parameters")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def init_database():
    """Initialize the database - called at app startup"""
    logger.info("Initializing database...")
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
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
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    else:
        logger.error("Could not initialize database - no connection")
        return False

# Initialize database when the app starts
init_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        message = request.form['message']
        
        if not all([name, surname, email, message]):
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
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
                logger.error(f"Database error: {e}")
                flash('Error sending message. Please try again.', 'error')
                return redirect(url_for('index'))
        else:
            flash('Database connection error!', 'error')
            return redirect(url_for('index'))

@app.route('/messages')
def view_messages():
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

@app.route('/health')
def health_check():
    return 'OK'

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return "Database connection successful!"
    else:
        return "Database connection failed!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port)