from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

def get_db_connection():
    """Create and return a PostgreSQL database connection"""
    try:
        # Try to get DATABASE_URL from environment (Render provides this)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Use the connection string from Render
            logger.info("Using DATABASE_URL from environment")
            # Fix for newer PostgreSQL connection strings
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            conn = psycopg2.connect(database_url)
        else:
            # Use local PostgreSQL development settings
            logger.info("Using local PostgreSQL development settings")
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'applications_db'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'Maxelo@2023'),
                port=os.environ.get('DB_PORT', '5432')
            )
        
        logger.info("PostgreSQL connection successful")
        return conn
        
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def init_database():
    """Initialize the PostgreSQL database"""
    logger.info("Initializing PostgreSQL database...")
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
            logger.info("PostgreSQL database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL database: {e}")
            return False
    else:
        logger.error("Could not initialize PostgreSQL database - no connection")
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
                logger.error(f"PostgreSQL error: {e}")
                flash('Error sending message. Please try again.', 'error')
                return redirect(url_for('index'))
        else:
            flash('PostgreSQL database connection error!', 'error')
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
            
            # Convert to list of dictionaries for template
            message_list = []
            for msg in messages:
                message_list.append({
                    'id': msg[0],
                    'name': msg[1],
                    'surname': msg[2],
                    'email': msg[3],
                    'message': msg[4],
                    'created_at': msg[5]
                })
                
            return render_template('messages.html', messages=message_list)
        except Exception as e:
            return f"Error retrieving messages: {str(e)}"
    else:
        return "PostgreSQL database connection error"

@app.route('/health')
def health_check():
    return 'OK'

@app.route('/test-db')
def test_db():
    """Test PostgreSQL database connection"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            cur.close()
            conn.close()
            return f"PostgreSQL connection successful!<br>Database version: {db_version[0]}"
        except Exception as e:
            return f"PostgreSQL connection failed: {str(e)}"
    else:
        return "PostgreSQL database connection failed!"

@app.route('/db-info')
def db_info():
    """Show PostgreSQL database information"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get message count
            cur.execute('SELECT COUNT(*) FROM messages')
            count = cur.fetchone()[0]
            
            # Get database name
            cur.execute('SELECT current_database()')
            db_name = cur.fetchone()[0]
            
            # Get PostgreSQL version
            cur.execute('SELECT version()')
            db_version = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return f"""
            <h2>PostgreSQL Database Information</h2>
            <p><strong>Database Name:</strong> {db_name}</p>
            <p><strong>PostgreSQL Version:</strong> {db_version.split(',')[0]}</p>
            <p><strong>Total Messages:</strong> {count}</p>
            <p><strong>Environment:</strong> {'Production (Render)' if os.environ.get('DATABASE_URL') else 'Development (Local)'}</p>
            """
        except Exception as e:
            return f"Error getting database info: {str(e)}"
    else:
        return "No PostgreSQL database connection"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)