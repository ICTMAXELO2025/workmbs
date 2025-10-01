from flask import Flask, render_template, request, redirect, url_for, flash
import pg8000
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

def get_db_connection():
    """Create and return a PostgreSQL database connection using pg8000"""
    try:
        # Try to get DATABASE_URL from environment (Render provides this)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Use the connection string from Render
            logger.info("Using DATABASE_URL from environment")
            
            # Parse DATABASE_URL format: postgresql://user:password@host:port/database
            if database_url.startswith('postgresql://'):
                # Remove the postgresql:// prefix
                url_parts = database_url.replace('postgresql://', '').split('@')
                if len(url_parts) != 2:
                    raise ValueError("Invalid DATABASE_URL format")
                    
                user_pass = url_parts[0].split(':')
                host_db = url_parts[1].split('/')
                if len(host_db) != 2:
                    raise ValueError("Invalid DATABASE_URL format")
                    
                host_port = host_db[0].split(':')
                
                # Extract components with safety checks
                username = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ''
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 5432
                database = host_db[1]
                
                conn = pg8000.connect(
                    user=username,
                    password=password,
                    host=host,
                    port=port,
                    database=database
                )
            elif database_url.startswith('postgres://'):
                # Handle older postgres:// format
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
                # Set environment variable for recursive call
                os.environ['DATABASE_URL'] = database_url
                return get_db_connection()
            else:
                # Fallback for other URL formats
                raise ValueError("Unsupported DATABASE_URL format")
                
        else:
            # Use local PostgreSQL development settings
            logger.info("Using local PostgreSQL development settings")
            conn = pg8000.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'applications_db'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'Maxelo@2023'),
                port=int(os.environ.get('DB_PORT', '5432'))
            )
        
        logger.info("PostgreSQL connection successful using pg8000")
        return conn
        
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database with pg8000: {e}")
        return None

def init_database():
    """Initialize the PostgreSQL database"""
    logger.info("Initializing PostgreSQL database...")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
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
            cursor.close()
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
        name = request.form.get('name', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        if not all([name, surname, email, message]):
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO messages (name, surname, email, message) VALUES (%s, %s, %s, %s)',
                    (name, surname, email, message)
                )
                conn.commit()
                cursor.close()
                conn.close()
                flash('Message sent successfully!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"PostgreSQL error: {e}")
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
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM messages ORDER BY created_at DESC')
            messages = cursor.fetchall()
            cursor.close()
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
                    'created_at': msg[5].strftime('%Y-%m-%d %H:%M:%S') if msg[5] else 'Unknown'
                })
                
            return render_template('messages.html', messages=message_list)
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return f"Error retrieving messages: {str(e)}"
    else:
        return "Database connection error"

@app.route('/health')
def health_check():
    return 'OK'

@app.route('/test-db')
def test_db():
    """Test PostgreSQL database connection"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT version()')
            db_version = cursor.fetchone()
            cursor.close()
            conn.close()
            return f"PostgreSQL connection successful using pg8000!<br>Database version: {db_version[0]}"
        except Exception as e:
            return f"PostgreSQL connection failed: {str(e)}"
    else:
        return "Database connection failed!"

@app.route('/db-info')
def db_info():
    """Show PostgreSQL database information"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get message count
            cursor.execute('SELECT COUNT(*) FROM messages')
            count = cursor.fetchone()[0]
            
            # Get database name
            cursor.execute('SELECT current_database()')
            db_name = cursor.fetchone()[0]
            
            # Get PostgreSQL version
            cursor.execute('SELECT version()')
            db_version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return f"""
            <h2>PostgreSQL Database Information</h2>
            <p><strong>Database Name:</strong> {db_name}</p>
            <p><strong>PostgreSQL Version:</strong> {db_version.split(',')[0]}</p>
            <p><strong>Total Messages:</strong> {count}</p>
            <p><strong>Driver:</strong> pg8000 (Pure Python)</p>
            <p><strong>Environment:</strong> {'Production (Render)' if os.environ.get('DATABASE_URL') else 'Development (Local)'}</p>
            """
        except Exception as e:
            return f"Error getting database info: {str(e)}"
    else:
        return "No database connection"

@app.errorhandler(404)
def not_found_error(error):
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)