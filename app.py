from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize Flask app first
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Database configuration - PostgreSQL only
def get_database_uri():
    """Get database URI based on environment"""
    # Check for PostgreSQL URL first (for production/Render)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Handle PostgreSQL URL format (especially for Render)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Fallback to local PostgreSQL for development
    return 'postgresql://postgres:Maxelo%402023@localhost:5432/managament_db'

app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Import models after app initialization
from models import db, Employee, Admin, LeaveRequest, Message, Todo, Document, AdminMessage, Announcement, MessageDocument, AdminMessageDocument, AdminAssignedTodo

# Initialize database with app
db.init_app(app)

def setup_database():
    """Setup database tables and initial data"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if we need to create initial admin user
            admin_exists = Admin.query.filter_by(email='admin@maxelo.com').first()
            if not admin_exists:
                # Create default admin user
                default_admin = Admin(
                    email='admin@maxelo.com',
                    password=generate_password_hash('admin123'),
                    name='System Administrator'
                )
                db.session.add(default_admin)
                db.session.commit()
                print("Default admin user created")
            
            print("PostgreSQL database setup completed successfully")
            
        except Exception as e:
            print(f"Database setup error: {e}")
            # Don't raise the error, just log it
            import traceback
            traceback.print_exc()

# Modern approach for database initialization
def initialize_database():
    """Initialize database when app starts"""
    try:
        with app.app_context():
            setup_database()
    except Exception as e:
        print(f"Database initialization note: {e}")
        print("This is normal if database isn't ready yet - tables will be created on first request")

# Initialize database (but don't crash if it fails)
initialize_database()

def login_required(role=None):
    """Decorator to require login and optionally specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('index'))
            
            if role and session.get('user_role') != role:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get the current user based on session"""
    if 'user_role' not in session or 'user_id' not in session:
        return None
    
    try:
        if session['user_role'] == 'admin':
            return Admin.query.get(session['user_id'])
        elif session['user_role'] == 'employee':
            return Employee.query.get(session['user_id'])
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None
    return None

def allowed_file(filename):
    """Check if file type is allowed"""
    if not filename:
        return False
    allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'pptx', 'ppt', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def format_file_size(size_in_bytes):
    """Format file size to human readable format"""
    if not size_in_bytes:
        return "0 Bytes"
    for unit in ['Bytes', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

# Make format_file_size available to all templates
app.jinja_env.globals.update(format_file_size=format_file_size)

def get_database_info():
    """Get database information for debugging"""
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'render.com' in db_uri:
        return 'PostgreSQL (Render)'
    elif 'localhost' in db_uri:
        return 'PostgreSQL (Local)'
    else:
        return 'PostgreSQL'

# Make database info available to templates
app.jinja_env.globals.update(get_database_info=get_database_info)

# Routes
@app.route('/')
def index():
    """Main index page with links to both login types"""
    return render_template('index.html')

import time
from flask import request
import logging

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        if elapsed > 1.0:  # Log slow requests (>1 second)
            logging.warning(f"Slow request: {request.path} took {elapsed:.2f}s")
    return response

# Authentication Routes
@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    if 'user_id' in session and session.get('user_role') == 'employee':
        return redirect(url_for('employee_dashboard'))
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password', 'error')
                return render_template('employee_login.html')
            
            employee = Employee.query.filter_by(email=email, is_active=True).first()
            
            if employee and check_password_hash(employee.password, password):
                # Clear any existing session
                session.clear()
                
                # Set new session
                session['user_id'] = employee.id
                session['user_role'] = 'employee'
                session['user_name'] = employee.name
                session['user_email'] = employee.email
                session.permanent = True
                
                employee.last_login = datetime.utcnow()
                db.session.commit()
                
                flash('Login successful!', 'success')
                return redirect(url_for('employee_dashboard'))
            else:
                flash('Invalid email or password', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash('Login failed. Please try again.', 'error')
    
    return render_template('employee_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session and session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password', 'error')
                return render_template('admin_login.html')
            
            admin = Admin.query.filter_by(email=email).first()
            
            if admin and check_password_hash(admin.password, password):
                session.clear()
                
                session['user_id'] = admin.id
                session['user_role'] = 'admin'
                session['user_name'] = admin.name
                session['user_email'] = admin.email
                session.permanent = True
                
                admin.last_login = datetime.utcnow()
                db.session.commit()
                
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash('Login failed. Please try again.', 'error')
    
    return render_template('admin_login.html')

# Quick Access Routes (for development/demo)
@app.route('/employee/quick')
def employee_quick_access():
    """Quick access for demo purposes"""
    key = request.args.get('key', '')
    if key == 'employee123':
        # Create or get demo employee
        demo_employee = Employee.query.filter_by(email='demo@employee.com').first()
        if not demo_employee:
            demo_employee = Employee(
                email='demo@employee.com',
                password=generate_password_hash('demo123'),
                name='Demo Employee',
                department='IT',
                position='Developer',
                is_active=True
            )
            db.session.add(demo_employee)
            db.session.commit()
        
        session.clear()
        session['user_id'] = demo_employee.id
        session['user_role'] = 'employee'
        session['user_name'] = demo_employee.name
        session['user_email'] = demo_employee.email
        
        flash('Demo employee login successful!', 'success')
        return redirect(url_for('employee_dashboard'))
    
    flash('Invalid quick access key', 'error')
    return redirect(url_for('employee_login'))

@app.route('/admin/quick')
def admin_quick_access():
    """Quick access for demo purposes"""
    key = request.args.get('key', '')
    if key == 'maxelo':
        # Create or get demo admin
        demo_admin = Admin.query.filter_by(email='admin@maxelo.com').first()
        if not demo_admin:
            demo_admin = Admin(
                email='admin@maxelo.com',
                password=generate_password_hash('admin123'),
                name='System Administrator'
            )
            db.session.add(demo_admin)
            db.session.commit()
        
        session.clear()
        session['user_id'] = demo_admin.id
        session['user_role'] = 'admin'
        session['user_name'] = demo_admin.name
        session['user_email'] = demo_admin.email
        
        flash('Demo admin login successful!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    flash('Invalid quick access key', 'error')
    return redirect(url_for('admin_login'))

# Logout Routes
@app.route('/logout')
def logout():
    """General logout route"""
    user_role = session.get('user_role')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    
    if user_role == 'admin':
        return redirect(url_for('admin_login'))
    else:
        return redirect(url_for('employee_login'))

# Employee Dashboard
@app.route('/employee/dashboard')
@login_required(role='employee')
def employee_dashboard():
    try:
        current_user = get_current_user()
        if not current_user:
            flash('User not found', 'error')
            return redirect(url_for('logout'))
        
        # Get statistics with proper error handling
        pending_leaves = LeaveRequest.query.filter_by(
            employee_id=current_user.id, 
            status='pending'
        ).count()
        
        unread_messages = Message.query.filter_by(
            receiver_id=current_user.id, 
            is_read=False
        ).count()
        
        pending_todos = Todo.query.filter_by(
            employee_id=current_user.id, 
            is_completed=False
        ).count()
        
        approved_leaves = LeaveRequest.query.filter_by(
            employee_id=current_user.id, 
            status='approved'
        ).count()
        
        # Get recent data
        recent_leaves = LeaveRequest.query.filter_by(
            employee_id=current_user.id
        ).order_by(LeaveRequest.created_at.desc()).limit(5).all()
        
        recent_messages = Message.query.filter_by(
            receiver_id=current_user.id
        ).order_by(Message.created_at.desc()).limit(5).all()
        
        upcoming_todos = Todo.query.filter_by(
            employee_id=current_user.id, 
            is_completed=False
        ).filter(Todo.due_date >= date.today()).order_by(
            Todo.due_date.asc()
        ).limit(5).all()
        
        recent_documents = Document.query.filter_by(
            employee_id=current_user.id
        ).order_by(Document.created_at.desc()).limit(3).all()
        
        admin_messages = AdminMessage.query.filter_by(
            sender_id=current_user.id
        ).order_by(AdminMessage.created_at.desc()).limit(2).all()
        
        announcements = Announcement.query.filter_by(
            is_active=True
        ).order_by(Announcement.created_at.desc()).limit(3).all()
        
        return render_template('employee_dashboard.html',
                             pending_leaves=pending_leaves,
                             unread_messages=unread_messages,
                             pending_todos=pending_todos,
                             approved_leaves=approved_leaves,
                             recent_leaves=recent_leaves,
                             recent_messages=recent_messages,
                             upcoming_todos=upcoming_todos,
                             recent_documents=recent_documents,
                             admin_messages=admin_messages,
                             announcements=announcements,
                             today=date.today(),
                             current_user=current_user)
                             
    except Exception as e:
        flash('Error loading dashboard', 'error')
        # Provide safe fallback values
        return render_template('employee_dashboard.html',
                             pending_leaves=0,
                             unread_messages=0,
                             pending_todos=0,
                             approved_leaves=0,
                             recent_leaves=[],
                             recent_messages=[],
                             upcoming_todos=[],
                             recent_documents=[],
                             admin_messages=[],
                             announcements=[],
                             today=date.today(),
                             current_user=get_current_user())

# Employee Leave Management
@app.route('/employee/leave')
@login_required(role='employee')
def employee_leave():
    current_user = get_current_user()
    leave_requests = LeaveRequest.query.filter_by(
        employee_id=current_user.id
    ).order_by(LeaveRequest.created_at.desc()).all()
    
    return render_template('employee_leave.html', 
                         leave_requests=leave_requests, 
                         current_user=current_user)

@app.route('/employee/leave/request', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_leave_request():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            leave_type = request.form.get('leave_type')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            reason = request.form.get('reason', '').strip()
            
            # Validation
            if not all([leave_type, start_date_str, end_date_str]):
                flash('Please fill in all required fields', 'error')
                return render_template('employee_leave_request.html', current_user=current_user)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            if start_date > end_date:
                flash('End date cannot be before start date', 'error')
                return render_template('employee_leave_request.html', current_user=current_user)
            
            if start_date < date.today():
                flash('Start date cannot be in the past', 'error')
                return render_template('employee_leave_request.html', current_user=current_user)
            
            leave_request = LeaveRequest(
                employee_id=current_user.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                status='pending'
            )
            
            db.session.add(leave_request)
            db.session.commit()
            flash('Leave request submitted successfully!', 'success')
            return redirect(url_for('employee_leave'))
            
        except ValueError:
            flash('Invalid date format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error submitting leave request', 'error')
    
    return render_template('employee_leave_request.html', current_user=current_user)

# Employee Messages
@app.route('/employee/messages')
@login_required(role='employee')
def employee_messages():
    current_user = get_current_user()
    messages = Message.query.filter_by(
        receiver_id=current_user.id
    ).order_by(Message.created_at.desc()).all()
    
    return render_template('employee_messages.html', 
                         messages=messages, 
                         current_user=current_user)

@app.route('/employee/messages/send', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_messages_send():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            receiver_id = request.form.get('receiver_id')
            subject = request.form.get('subject', '').strip()
            content = request.form.get('content', '').strip()
            
            if not all([receiver_id, subject, content]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('employee_messages_send'))
            
            # Check if receiver exists and is not the current user
            receiver = Employee.query.filter_by(id=receiver_id, is_active=True).first()
            if not receiver:
                flash('Invalid recipient selected', 'error')
                return redirect(url_for('employee_messages_send'))
            
            if receiver.id == current_user.id:
                flash('You cannot send messages to yourself', 'error')
                return redirect(url_for('employee_messages_send'))
            
            message = Message(
                sender_id=current_user.id,
                receiver_id=receiver_id,
                subject=subject,
                content=content
            )
            
            db.session.add(message)
            db.session.commit()
            flash('Message sent successfully!', 'success')
            return redirect(url_for('employee_messages'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error sending message', 'error')
    
    # Get active employees for recipient selection (excluding current user)
    employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.id != current_user.id
    ).all()
    
    # Get recent contacts (last 5 people messaged)
    recent_contacts = Employee.query.join(
        Message, Employee.id == Message.receiver_id
    ).filter(
        Message.sender_id == current_user.id
    ).distinct().limit(5).all()
    
    return render_template('employee_messages_send.html',
                         employees=employees,
                         recent_contacts=recent_contacts,
                         current_user=current_user)

# Employee Documents
@app.route('/employee/documents')
@login_required(role='employee')
def employee_documents():
    current_user = get_current_user()
    documents = Document.query.filter_by(
        employee_id=current_user.id
    ).order_by(Document.created_at.desc()).all()
    
    return render_template('employee_documents.html', 
                         documents=documents, 
                         current_user=current_user)

@app.route('/employee/documents/upload', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_documents_upload():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('employee_documents_upload'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('employee_documents_upload'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Get file size without reading entire file
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()  # Get position (file size)
                file.seek(0)  # Reset to beginning
                
                document = Document(
                    employee_id=current_user.id,
                    filename=filename,
                    original_filename=filename,
                    file_path=f"/uploads/{filename}",  # Placeholder
                    file_size=file_size,
                    description=request.form.get('description', '').strip(),
                    uploaded_by_admin=False
                )
                
                db.session.add(document)
                db.session.commit()
                flash('Document uploaded successfully!', 'success')
                return redirect(url_for('employee_documents'))
            else:
                flash('Invalid file type. Please check allowed formats.', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash('Error uploading document', 'error')
    
    return render_template('employee_documents_upload.html', current_user=current_user)

# Employee Todos
@app.route('/employee/todos')
@login_required(role='employee')
def employee_todos():
    try:
        current_user = get_current_user()
        if not current_user:
            flash('User not found', 'error')
            return redirect(url_for('logout'))
        
        # Get all todos for the current user
        todos = Todo.query.filter_by(
            employee_id=current_user.id
        ).order_by(
            Todo.is_completed.asc(),
            Todo.due_date.asc(),
            Todo.priority.desc()
        ).all()
        
        # Categorize todos for better organization
        pending_todos = [todo for todo in todos if not todo.is_completed]
        completed_todos = [todo for todo in todos if todo.is_completed]
        high_priority_todos = [todo for todo in pending_todos if todo.priority in ['high', 'urgent']]
        overdue_todos = [todo for todo in pending_todos if todo.due_date and todo.due_date < date.today()]
        
        # Get counts for the sidebar
        pending_todos_count = len(pending_todos)
        unread_messages_count = Message.query.filter_by(
            receiver_id=current_user.id, 
            is_read=False
        ).count()
        
        return render_template('employee_todos.html', 
                             todos=todos,
                             pending_todos=pending_todos,
                             completed_todos=completed_todos,
                             high_priority_todos=high_priority_todos,
                             overdue_todos=overdue_todos,
                             pending_todos_count=pending_todos_count,
                             unread_messages_count=unread_messages_count,
                             today=date.today(),
                             current_user=current_user)
                             
    except Exception as e:
        print(f"Error in employee_todos: {e}")
        flash('Error loading tasks. Please try again.', 'error')
        # Provide safe fallback values
        return render_template('employee_todos.html',
                             todos=[],
                             pending_todos=[],
                             completed_todos=[],
                             high_priority_todos=[],
                             overdue_todos=[],
                             pending_todos_count=0,
                             unread_messages_count=0,
                             today=date.today(),
                             current_user=get_current_user())
@app.route('/employee/todo/<int:todo_id>/edit', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_todo_edit(todo_id):
    current_user = get_current_user()
    
    todo = Todo.query.filter_by(id=todo_id, employee_id=current_user.id).first()
    if not todo:
        flash('Task not found', 'error')
        return redirect(url_for('employee_todos'))
    
    if request.method == 'POST':
        try:
            todo.content = request.form.get('content', '').strip()
            todo.priority = request.form.get('priority', 'medium')
            todo.category = request.form.get('category', '')
            todo.is_important = 'is_important' in request.form
            
            due_date_str = request.form.get('due_date')
            todo.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('employee_todos'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating task', 'error')
    
    return render_template('employee_todo_edit.html', 
                         todo=todo,
                         current_user=current_user,
                         today=date.today())

@app.route('/employee/todos/clear-completed', methods=['POST'])
@login_required(role='employee')
def employee_todos_clear_completed():
    current_user = get_current_user()
    
    try:
        completed_todos = Todo.query.filter_by(
            employee_id=current_user.id,
            is_completed=True
        ).all()
        
        for todo in completed_todos:
            db.session.delete(todo)
        
        db.session.commit()
        flash(f'Cleared {len(completed_todos)} completed tasks!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error clearing completed tasks', 'error')
    
    return redirect(url_for('employee_todos'))

@app.route('/employee/todos/add', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_todos_add():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            content = request.form.get('content', '').strip()
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            category = request.form.get('category', '')
            is_important = 'is_important' in request.form
            
            if not content:
                flash('Task description is required', 'error')
                return render_template('employee_todos_add.html', 
                                     current_user=current_user,
                                     today=date.today(),
                                     user_role='employee')
            
            due_date = None
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date < date.today():
                    flash('Due date cannot be in the past', 'error')
                    return render_template('employee_todos_add.html',
                                         current_user=current_user,
                                         today=date.today(),
                                         user_role='employee')
            
            todo = Todo(
                employee_id=current_user.id,
                content=content,
                priority=priority,
                due_date=due_date,
                category=category,
                is_important=is_important
            )
            
            db.session.add(todo)
            db.session.commit()
            flash('Task added successfully!', 'success')
            return redirect(url_for('employee_todos'))
            
        except ValueError:
            flash('Invalid date format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error adding task', 'error')
    
    return render_template('task_form.html',  # Updated template name
                         current_user=current_user,
                         today=date.today(),
                         user_role='employee')

@app.route('/employee/todo/<int:todo_id>/update', methods=['POST'])
@login_required(role='employee')
def employee_todo_update(todo_id):
    current_user = get_current_user()
    
    try:
        todo = Todo.query.filter_by(id=todo_id, employee_id=current_user.id).first()
        if not todo:
            flash('Task not found', 'error')
            return redirect(url_for('employee_todos'))
        
        todo.is_completed = not todo.is_completed
        db.session.commit()
        flash('Task updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating task', 'error')
    
    return redirect(url_for('employee_todos'))

@app.route('/employee/todo/<int:todo_id>/delete')
@login_required(role='employee')
def employee_todo_delete(todo_id):
    current_user = get_current_user()
    
    try:
        todo = Todo.query.filter_by(id=todo_id, employee_id=current_user.id).first()
        if not todo:
            flash('Task not found', 'error')
            return redirect(url_for('employee_todos'))
        
        db.session.delete(todo)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting task', 'error')
    
    return redirect(url_for('employee_todos'))

# Admin Dashboard
@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    current_user = get_current_user()
    
    try:
        total_employees = Employee.query.filter_by(is_active=True).count()
        pending_leave_requests = LeaveRequest.query.filter_by(status='pending').count()
        unread_admin_messages = AdminMessage.query.filter_by(is_read=False).count()
        active_employees = Employee.query.filter_by(is_active=True).count()
        pending_tasks_count = Todo.query.filter_by(is_completed=False).count()
        total_documents = Document.query.count()
        
        pending_leaves = LeaveRequest.query.filter_by(status='pending').options(
            db.joinedload(LeaveRequest.employee)
        ).order_by(LeaveRequest.created_at.desc()).limit(5).all()
        
        recent_messages = AdminMessage.query.options(
            db.joinedload(AdminMessage.sender)
        ).order_by(AdminMessage.created_at.desc()).limit(3).all()
        
        return render_template('admin_dashboard.html',
                             total_employees=total_employees,
                             pending_leave_requests=pending_leave_requests,
                             unread_admin_messages=unread_admin_messages,
                             active_employees=active_employees,
                             pending_tasks_count=pending_tasks_count,
                             total_documents=total_documents,
                             pending_leaves=pending_leaves,
                             recent_messages=recent_messages,
                             current_user=current_user)
                             
    except Exception as e:
        flash('Error loading admin dashboard', 'error')
        return render_template('admin_dashboard.html',
                             total_employees=0,
                             pending_leave_requests=0,
                             unread_admin_messages=0,
                             active_employees=0,
                             pending_tasks_count=0,
                             total_documents=0,
                             pending_leaves=[],
                             recent_messages=[],
                             current_user=current_user)
    current_user = get_current_user()
    
    try:
        total_employees = Employee.query.filter_by(is_active=True).count()
        pending_leave_requests = LeaveRequest.query.filter_by(status='pending').count()
        unread_admin_messages = AdminMessage.query.filter_by(is_read=False).count()
        active_employees = Employee.query.filter_by(is_active=True).count()
        
        pending_leaves = LeaveRequest.query.filter_by(status='pending').order_by(
            LeaveRequest.created_at.desc()
        ).limit(5).all()
        
        recent_messages = AdminMessage.query.options(
            db.joinedload(AdminMessage.sender)
        ).order_by(AdminMessage.created_at.desc()).limit(5).all()
        
        return render_template('admin_dashboard.html',
                             total_employees=total_employees,
                             pending_leave_requests=pending_leave_requests,
                             unread_admin_messages=unread_admin_messages,
                             active_employees=active_employees,
                             pending_leaves=pending_leaves,
                             recent_messages=recent_messages,
                             current_user=current_user)
                             
    except Exception as e:
        flash('Error loading admin dashboard', 'error')
        return render_template('admin_dashboard.html',
                             total_employees=0,
                             pending_leave_requests=0,
                             unread_admin_messages=0,
                             active_employees=0,
                             pending_leaves=[],
                             recent_messages=[],
                             current_user=current_user)

# Admin Employee Management
@app.route('/admin/employees')
@login_required(role='admin')
def admin_employees():
    current_user = get_current_user()
    employees = Employee.query.order_by(Employee.name.asc()).all()
    
    return render_template('admin_employees.html',
                         employees=employees,
                         current_user=current_user)

@app.route('/admin/employees/add', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_employees_add():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', '').strip()
            position = request.form.get('position', '').strip()
            hire_date_str = request.form.get('hire_date')
            
            if not all([name, email, password]):
                flash('Please fill in all required fields', 'error')
                return render_template('admin_employees_add.html', current_user=current_user)
            
            # Check if email already exists
            existing_employee = Employee.query.filter_by(email=email).first()
            if existing_employee:
                flash('Email already exists', 'error')
                return render_template('admin_employees_add.html', current_user=current_user)
            
            hire_date = date.today()
            if hire_date_str:
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            
            employee = Employee(
                name=name,
                email=email,
                password=generate_password_hash(password),
                phone=phone,
                department=department,
                position=position,
                hire_date=hire_date,
                is_active=True
            )
            
            db.session.add(employee)
            db.session.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('admin_employees'))
            
        except ValueError:
            flash('Invalid date format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error adding employee', 'error')
    
    return render_template('admin_employees_add.html', current_user=current_user)

@app.route('/admin/employee/<int:employee_id>/toggle')
@login_required(role='admin')
def admin_employee_toggle_status(employee_id):
    current_user = get_current_user()
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        employee.is_active = not employee.is_active
        db.session.commit()
        
        status = "activated" if employee.is_active else "deactivated"
        flash(f'Employee {status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating employee status', 'error')
    
    return redirect(url_for('admin_employees'))

@app.route('/admin/employee/<int:employee_id>/delete')
@login_required(role='admin')
def admin_employee_delete(employee_id):
    current_user = get_current_user()
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting employee', 'error')
    
    return redirect(url_for('admin_employees'))

# Admin Leave Management
@app.route('/admin/leave-requests')
@login_required(role='admin')
def admin_leave_requests():
    current_user = get_current_user()
    leave_requests = LeaveRequest.query.options(
        db.joinedload(LeaveRequest.employee)
    ).order_by(LeaveRequest.created_at.desc()).all()
    
    return render_template('admin_leave_requests.html',
                         leave_requests=leave_requests,
                         current_user=current_user)

@app.route('/admin/leave-request/<int:request_id>/update')
@login_required(role='admin')
def admin_leave_request_update(request_id):
    current_user = get_current_user()
    
    try:
        status = request.args.get('status')
        if status not in ['approved', 'rejected']:
            flash('Invalid status', 'error')
            return redirect(url_for('admin_leave_requests'))
        
        leave_request = LeaveRequest.query.get_or_404(request_id)
        leave_request.status = status
        db.session.commit()
        
        flash(f'Leave request {status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating leave request', 'error')
    
    return redirect(url_for('admin_leave_requests'))

# Profile Management
@app.route('/profile')
@login_required()
def profile():
    current_user = get_current_user()
    if not current_user:
        flash('User not found', 'error')
        return redirect(url_for('logout'))
    
    extra_data = {}
    if session.get('user_role') == 'admin':
        extra_data['employees_count'] = Employee.query.filter_by(is_active=True).count()
        extra_data['pending_leaves_count'] = LeaveRequest.query.filter_by(status='pending').count()
    
    return render_template('profile.html', current_user=current_user, **extra_data)

@app.route('/profile/update', methods=['POST'])
@login_required()
def update_profile():
    current_user = get_current_user()
    if not current_user:
        flash('User not found', 'error')
        return redirect(url_for('logout'))
    
    try:
        current_user.name = request.form.get('name', current_user.name)
        
        if session.get('user_role') == 'employee':
            current_user.phone = request.form.get('phone', current_user.phone)
        
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if new_password:
            if new_password == confirm_password:
                if len(new_password) >= 6:
                    current_user.password = generate_password_hash(new_password)
                    flash('Password updated successfully!', 'success')
                else:
                    flash('Password must be at least 6 characters long', 'error')
                    return redirect(url_for('profile'))
            else:
                flash('Passwords do not match', 'error')
                return redirect(url_for('profile'))
        
        db.session.commit()
        session['user_name'] = current_user.name  # Update session
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile', 'error')
    
    return redirect(url_for('profile'))

# Admin Message Management
@app.route('/admin/messages')
@login_required(role='admin')
def admin_messages():
    current_user = get_current_user()
    messages = AdminMessage.query.options(
        db.joinedload(AdminMessage.sender)
    ).order_by(AdminMessage.created_at.desc()).all()
    
    return render_template('admin_messages.html',
                         messages=messages,
                         current_user=current_user)

@app.route('/admin/message/<int:message_id>/respond', methods=['POST'])
@login_required(role='admin')
def admin_message_respond(message_id):
    current_user = get_current_user()
    
    try:
        message = AdminMessage.query.get_or_404(message_id)
        response = request.form.get('response', '').strip()
        
        if not response:
            flash('Response cannot be empty', 'error')
            return redirect(url_for('admin_messages'))
        
        message.admin_response = response
        message.is_read = True
        message.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Response sent successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error sending response', 'error')
    
    return redirect(url_for('admin_messages'))

@app.route('/admin/message/<int:message_id>/mark-read')
@login_required(role='admin')
def admin_message_mark_read(message_id):
    current_user = get_current_user()
    
    try:
        message = AdminMessage.query.get_or_404(message_id)
        message.is_read = True
        message.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Message marked as read', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating message', 'error')
    
    return redirect(url_for('admin_messages'))

# Admin Send Message to Employees
@app.route('/admin/send-message', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_send_message():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            recipient_type = request.form.get('recipient_type', 'all')
            subject = request.form.get('subject', '').strip()
            content = request.form.get('content', '').strip()
            
            if not all([subject, content]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('admin_send_message'))
            
            # Get recipients based on selection
            if recipient_type == 'all':
                recipients = Employee.query.filter_by(is_active=True).all()
                selected_employees = request.form.getlist('selected_employees')
                if selected_employees:
                    recipients = Employee.query.filter(
                        Employee.id.in_(selected_employees),
                        Employee.is_active == True
                    ).all()
            else:
                selected_employees = request.form.getlist('selected_employees')
                if not selected_employees:
                    flash('Please select at least one employee', 'error')
                    return redirect(url_for('admin_send_message'))
                recipients = Employee.query.filter(
                    Employee.id.in_(selected_employees),
                    Employee.is_active == True
                ).all()
            
            if not recipients:
                flash('No valid recipients selected', 'error')
                return redirect(url_for('admin_send_message'))
            
            # Create messages for each recipient
            for recipient in recipients:
                message = Message(
                    sender_id=current_user.id,  # Admin sending as themselves
                    receiver_id=recipient.id,
                    subject=subject,
                    content=content
                )
                db.session.add(message)
            
            db.session.commit()
            flash(f'Message sent to {len(recipients)} employee(s) successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error sending message', 'error')
    
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name.asc()).all()
    return render_template('admin_send_message.html',
                         employees=employees,
                         current_user=current_user)

# Admin Document Management
@app.route('/admin/documents')
@login_required(role='admin')
def admin_documents():
    current_user = get_current_user()
    documents = Document.query.options(
        db.joinedload(Document.employee),
        db.joinedload(Document.admin)
    ).order_by(Document.created_at.desc()).all()
    
    recent_documents = Document.query.options(
        db.joinedload(Document.employee)
    ).order_by(Document.created_at.desc()).limit(5).all()
    
    return render_template('admin_documents.html',
                         documents=documents,
                         recent_documents=recent_documents,
                         current_user=current_user)

@app.route('/admin/documents/add', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_document_add():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            description = request.form.get('description', '').strip()
            document_type = request.form.get('doc_type', 'other')
            tags = request.form.get('tags', '').strip()
            send_notification = 'send_notification' in request.form
            is_important = 'is_important' in request.form
            
            if not employee_id or not description:
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('admin_document_add'))
            
            if 'document' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('admin_document_add'))
            
            file = request.files['document']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('admin_document_add'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Get file size without reading entire file
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)
                
                document = Document(
                    employee_id=employee_id,
                    filename=filename,
                    original_filename=filename,
                    file_path=f"/uploads/{filename}",  # Placeholder
                    file_size=file_size,
                    description=description,
                    document_type=document_type,
                    tags=tags,
                    is_important=is_important,
                    uploaded_by_admin=True,
                    admin_id=current_user.id
                )
                
                db.session.add(document)
                db.session.commit()
                
                if send_notification:
                    # In production, send email notification
                    pass
                
                flash('Document uploaded successfully!', 'success')
                return redirect(url_for('admin_documents'))
            else:
                flash('Invalid file type. Please check allowed formats.', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash('Error uploading document', 'error')
    
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name.asc()).all()
    recent_documents = Document.query.options(
        db.joinedload(Document.employee)
    ).order_by(Document.created_at.desc()).limit(5).all()
    
    return render_template('admin_document_add.html',
                         employees=employees,
                         recent_documents=recent_documents,
                         current_user=current_user)

# Admin Todo Management
@app.route('/admin/todo/add', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_todo_add():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            content = request.form.get('content', '').strip()
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            send_notification = 'send_notification' in request.form
            
            if not all([employee_id, content]):
                flash('Please fill in all required fields', 'error')
                return render_template('task_form.html',
                                     employees=employees,
                                     current_user=current_user,
                                     today=date.today(),
                                     user_role='admin')
            
            due_date = None
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date < date.today():
                    flash('Due date cannot be in the past', 'error')
                    return render_template('task_form.html',
                                         employees=employees,
                                         current_user=current_user,
                                         today=date.today(),
                                         user_role='admin')
            
            # Create admin assigned todo
            admin_todo = AdminAssignedTodo(
                admin_id=current_user.id,
                employee_id=employee_id,
                content=content,
                priority=priority,
                due_date=due_date
            )
            
            # Also create a regular todo for the employee
            employee_todo = Todo(
                employee_id=employee_id,
                content=f"[From Admin] {content}",
                priority=priority,
                due_date=due_date,
                assigned_by_admin=True
            )
            
            db.session.add(admin_todo)
            db.session.add(employee_todo)
            db.session.commit()
            
            if send_notification:
                # In production, send email notification
                pass
            
            flash('Task assigned successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except ValueError:
            flash('Invalid date format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error assigning task', 'error')
    
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name.asc()).all()
    return render_template('task_form.html',
                         employees=employees,
                         current_user=current_user,
                         today=date.today(),
                         user_role='admin')
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            content = request.form.get('content', '').strip()
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            
            if not all([employee_id, content]):
                flash('Please fill in all required fields', 'error')
                return render_template('admin_todo_add.html', current_user=current_user)
            
            due_date = None
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date < date.today():
                    flash('Due date cannot be in the past', 'error')
                    return render_template('admin_todo_add.html', current_user=current_user)
            
            # Create admin assigned todo
            admin_todo = AdminAssignedTodo(
                admin_id=current_user.id,
                employee_id=employee_id,
                content=content,
                priority=priority,
                due_date=due_date
            )
            
            # Also create a regular todo for the employee
            employee_todo = Todo(
                employee_id=employee_id,
                content=f"[From Admin] {content}",
                priority=priority,
                due_date=due_date
            )
            
            db.session.add(admin_todo)
            db.session.add(employee_todo)
            db.session.commit()
            
            flash('Task assigned successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except ValueError:
            flash('Invalid date format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error assigning task', 'error')
    
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name.asc()).all()
    return render_template('admin_todo_add.html',
                         employees=employees,
                         today=date.today(),
                         current_user=current_user)

# Employee Admin Messages
@app.route('/employee/admin-messages')
@login_required(role='employee')
def employee_admin_messages():
    current_user = get_current_user()
    messages = AdminMessage.query.filter_by(
        sender_id=current_user.id
    ).order_by(AdminMessage.created_at.desc()).all()
    
    return render_template('employee_admin_messages.html',
                         messages=messages,
                         current_user=current_user)

@app.route('/employee/admin-messages/send', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_admin_messages_send():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            subject = request.form.get('subject', '').strip()
            content = request.form.get('content', '').strip()
            
            if not all([subject, content]):
                flash('Please fill in all required fields', 'error')
                return render_template('employee_admin_messages_send.html', current_user=current_user)
            
            message = AdminMessage(
                sender_id=current_user.id,
                subject=subject,
                content=content
            )
            
            db.session.add(message)
            db.session.commit()
            flash('Message sent to admin successfully!', 'success')
            return redirect(url_for('employee_admin_messages'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error sending message to admin', 'error')
    
    return render_template('employee_admin_messages_send.html', current_user=current_user)

# Document Download Routes
@app.route('/employee/document/<int:doc_id>/download')
@login_required(role='employee')
def employee_document_download(doc_id):
    current_user = get_current_user()
    
    try:
        document = Document.query.filter_by(id=doc_id, employee_id=current_user.id).first()
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('employee_documents'))
        
        # In production, serve the actual file
        flash('Download functionality would be implemented in production', 'info')
        return redirect(url_for('employee_documents'))
        
    except Exception as e:
        flash('Error downloading document', 'error')
        return redirect(url_for('employee_documents'))

@app.route('/employee/document/<int:doc_id>/delete')
@login_required(role='employee')
def employee_document_delete(doc_id):
    current_user = get_current_user()
    
    try:
        document = Document.query.filter_by(id=doc_id, employee_id=current_user.id).first()
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('employee_documents'))
        
        db.session.delete(document)
        db.session.commit()
        flash('Document deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting document', 'error')
    
    return redirect(url_for('employee_documents'))

# Forgot Password Routes
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('forgot_password.html')
        
        # In production, send reset email
        flash('If an account exists with this email, a password reset link has been sent.', 'info')
        return redirect(url_for('employee_login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return render_template('reset_password.html')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('reset_password.html')
        
        # In production, update password in database
        flash('Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('employee_login'))
    
    return render_template('reset_password.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

# Health check route
@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy', 
            'database': 'connected',
            'database_type': get_database_info()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy', 
            'error': str(e),
            'database_type': get_database_info()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)