from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Employee, LeaveRequest, Message, Document, Todo, AdminMessage
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import io
import logging

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration - Use SQLite for local development
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres'):
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("Using PostgreSQL database from environment")
else:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "management.db")}'
    print("Using SQLite database for local development")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Enhanced Session Configuration for multiple tabs
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'xlsx', 'xls', 'pptx', 'ppt', 'csv'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Session refresh middleware for multiple tabs
@app.before_request
def refresh_session():
    if 'user_id' in session:
        session.modified = True

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(size):
    """Convert file size to human readable format"""
    if size is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

# Context processor to make functions available in all templates
@app.context_processor
def utility_processor():
    return dict(format_file_size=format_file_size, date=date, datetime=datetime)

def login_required(role=None):
    """Decorator to require login and optionally check role"""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                if role == 'admin':
                    return redirect(url_for('admin_login'))
                else:
                    return redirect(url_for('employee_login'))
            
            # Verify the user still exists and is active
            current_user = get_current_user()
            if not current_user:
                session.clear()
                flash('Your session has expired. Please log in again.', 'error')
                if role == 'admin':
                    return redirect(url_for('admin_login'))
                else:
                    return redirect(url_for('employee_login'))
            
            if role and session.get('user_role') != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('employee_login'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current user from session with error handling"""
    if 'user_id' not in session:
        return None
    
    user_id = session['user_id']
    user_role = session.get('user_role')
    
    try:
        if user_role == 'admin':
            return Admin.query.get(user_id)
        elif user_role == 'employee':
            return Employee.query.get(user_id)
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None
    
    return None

# Create tables and initial data
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
        
        # Create default admin if not exists
        if not Admin.query.filter_by(email='admin@maxelo.co.za').first():
            default_admin = Admin(
                email='admin@maxelo.co.za',
                password=generate_password_hash('admin123'),
                name='System Administrator'
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin created")
        
        # Create default employee if not exists
        if not Employee.query.filter_by(email='mavis@maxelo.com').first():
            default_employee = Employee(
                email='mavis@maxelo.com',
                password=generate_password_hash('123admin'),
                name='Mavis',
                department='Operations',
                position='Staff',
                hire_date=date.today()
            )
            db.session.add(default_employee)
            db.session.commit()
            print("Default employee created")
        
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        db.session.rollback()

# Test database connection
try:
    with app.app_context():
        db.engine.connect()
        print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Routes
@app.route('/')
def index():
    """Main index page with links to both login types"""
    return render_template('e')

# Employee Authentication Routes
@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    if 'user_id' in session and session.get('user_role') == 'employee':
        return redirect(url_for('employee_dashboard'))
            
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        employee = Employee.query.filter_by(email=email, is_active=True).first()
        
        if employee and check_password_hash(employee.password, password):
            # Clear any existing session completely
            session.clear()
            
            # Set session with proper configuration
            session['user_id'] = employee.id
            session['user_role'] = 'employee'
            session['user_name'] = employee.name
            session['user_email'] = employee.email
            session.permanent = True
            
            # Force session to save
            session.modified = True
            
            employee.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Employee login successful!', 'success')
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('employee_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session and session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
            
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password, password):
            # Clear any existing session completely
            session.clear()
            
            # Set session with proper configuration
            session['user_id'] = admin.id
            session['user_role'] = 'admin'
            session['user_name'] = admin.name
            session['user_email'] = admin.email
            session.permanent = True
            
            # Force session to save
            session.modified = True
            
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    
    return render_template('admin_login.html')

# Separate logout routes
@app.route('/employee/logout')
def employee_logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('employee_login'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

# Password reset routes
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        email = session.get('reset_email')
        if email:
            employee = Employee.query.filter_by(email=email, is_active=True).first()
            if employee:
                employee.password = generate_password_hash(new_password)
                db.session.commit()
                session.pop('reset_email', None)
                flash('Password reset successfully! You can now log in with your new password.', 'success')
                return redirect(url_for('employee_login'))
        
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password'))
    
    return render_template('reset_password.html', token=token)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        employee = Employee.query.filter_by(email=email, is_active=True).first()
        
        if employee:
            session['reset_email'] = email
            flash('Please set your new password below.', 'info')
            return redirect(url_for('reset_password', token='demo-token'))
        else:
            flash('Email not found in our system.', 'error')
    
    return render_template('forgot_password.html')

# Employee Dashboard Routes
@app.route('/employee/dashboard')
@login_required(role='employee')
def employee_dashboard():
    try:
        current_user = get_current_user()
        
        # Get employee statistics
        pending_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id, status='pending').count()
        unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        pending_todos = Todo.query.filter_by(employee_id=current_user.id, is_completed=False).count()
        approved_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id, status='approved').count()
        
        # Get recent leave requests
        recent_leaves = LeaveRequest.query.filter_by(employee_id=current_user.id)\
            .order_by(LeaveRequest.created_at.desc()).limit(5).all()
        
        # Get recent messages
        recent_messages = Message.query.filter_by(receiver_id=current_user.id)\
            .order_by(Message.created_at.desc()).limit(5).all()
        
        # Get employees for messaging
        employees = Employee.query.filter(Employee.id != current_user.id, Employee.is_active == True).all()
        
        # Get upcoming todos
        upcoming_todos = Todo.query.filter_by(employee_id=current_user.id, is_completed=False)\
            .filter(Todo.due_date >= date.today())\
            .order_by(Todo.due_date.asc()).limit(5).all()
        
        return render_template('employee_dashboard.html',
                             pending_leaves=pending_leaves,
                             unread_messages=unread_messages,
                             pending_todos=pending_todos,
                             approved_leaves=approved_leaves,
                             recent_leaves=recent_leaves,
                             recent_messages=recent_messages,
                             employees=employees,
                             upcoming_todos=upcoming_todos,
                             today=date.today(),
                             current_user=current_user)
    except Exception as e:
        flash('Error loading dashboard data', 'error')
        current_user = get_current_user()
        return render_template('employee_dashboard.html',
                             pending_leaves=0,
                             unread_messages=0,
                             pending_todos=0,
                             approved_leaves=0,
                             recent_leaves=[],
                             recent_messages=[],
                             employees=[],
                             upcoming_todos=[],
                             today=date.today(),
                             current_user=current_user)

# Employee Leave Routes
@app.route('/employee/leave')
@login_required(role='employee')
def employee_leave():
    current_user = get_current_user()
    leave_requests = LeaveRequest.query.filter_by(employee_id=current_user.id).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('employee_leave.html', leave_requests=leave_requests, current_user=current_user)

@app.route('/employee/leave/request', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_leave_request():
    current_user = get_current_user()
    if request.method == 'POST':
        try:
            leave_type = request.form.get('leave_type')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            reason = request.form.get('reason')
            
            leave_request = LeaveRequest(
                employee_id=current_user.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason
            )
            
            db.session.add(leave_request)
            db.session.commit()
            flash('Leave request submitted successfully!', 'success')
            return redirect(url_for('employee_leave'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting leave request.', 'error')
    
    return render_template('employee_leave_request.html', current_user=current_user)

# Employee Messages Routes
@app.route('/employee/messages')
@login_required(role='employee')
def employee_messages():
    current_user = get_current_user()
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('employee_messages.html', messages=messages, current_user=current_user)

@app.route('/employee/messages/send', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_messages_send():
    current_user = get_current_user()
    employees = Employee.query.filter(Employee.id != current_user.id, Employee.is_active == True).all()
    
    if request.method == 'POST':
        try:
            receiver_id = request.form.get('receiver_id')
            subject = request.form.get('subject')
            content = request.form.get('content')
            
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
            flash('Error sending message.', 'error')
    
    return render_template('employee_messages_send.html', employees=employees, current_user=current_user)

@app.route('/messages/<int:message_id>/read', methods=['POST'])
@login_required(role='employee')
def mark_message_read(message_id):
    current_user = get_current_user()
    message = Message.query.filter_by(id=message_id, receiver_id=current_user.id).first()
    
    if message:
        try:
            message.is_read = True
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Message not found'})

# Employee Documents Routes
@app.route('/employee/documents')
@login_required(role='employee')
def employee_documents():
    current_user = get_current_user()
    documents = Document.query.filter_by(employee_id=current_user.id).order_by(Document.created_at.desc()).all()
    return render_template('employee_documents.html', documents=documents, current_user=current_user)

@app.route('/employee/documents/upload', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_documents_upload():
    current_user = get_current_user()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                unique_filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                document = Document(
                    employee_id=current_user.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    description=request.form.get('description', '')
                )
                
                db.session.add(document)
                db.session.commit()
                flash('Document uploaded successfully!', 'success')
                return redirect(url_for('employee_documents'))
            except Exception as e:
                db.session.rollback()
                flash('Error uploading document.', 'error')
        else:
            flash('File type not allowed.', 'error')
    
    return render_template('employee_documents_upload.html', current_user=current_user)

@app.route('/employee/documents/<int:doc_id>/download')
@login_required(role='employee')
def employee_document_download(doc_id):
    current_user = get_current_user()
    document = Document.query.filter_by(id=doc_id, employee_id=current_user.id).first_or_404()
    
    try:
        return send_file(document.file_path, as_attachment=True, download_name=document.original_filename)
    except Exception as e:
        flash('Error downloading file.', 'error')
        return redirect(url_for('employee_documents'))

@app.route('/employee/documents/<int:doc_id>/delete')
@login_required(role='employee')
def employee_document_delete(doc_id):
    current_user = get_current_user()
    document = Document.query.filter_by(id=doc_id, employee_id=current_user.id).first_or_404()
    
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.session.delete(document)
        db.session.commit()
        flash('Document deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting document.', 'error')
    
    return redirect(url_for('employee_documents'))

# Employee Todo Routes
@app.route('/employee/todos')
@login_required(role='employee')
def employee_todos():
    current_user = get_current_user()
    todos = Todo.query.filter_by(employee_id=current_user.id).order_by(Todo.due_date.asc()).all()
    return render_template('employee_todos.html', todos=todos, current_user=current_user)

@app.route('/employee/todos/add', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_todos_add():
    current_user = get_current_user()
    if request.method == 'POST':
        try:
            content = request.form.get('content')
            priority = request.form.get('priority', 'medium')
            due_date_str = request.form.get('due_date')
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            
            todo = Todo(
                employee_id=current_user.id,
                content=content,
                priority=priority,
                due_date=due_date
            )
            
            db.session.add(todo)
            db.session.commit()
            flash('Task added successfully!', 'success')
            return redirect(url_for('employee_todos'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding task.', 'error')
    
    return render_template('employee_todos_add.html', current_user=current_user)

@app.route('/employee/todos/<int:todo_id>/update', methods=['POST'])
@login_required(role='employee')
def employee_todo_update(todo_id):
    current_user = get_current_user()
    todo = Todo.query.filter_by(id=todo_id, employee_id=current_user.id).first_or_404()
    
    try:
        todo.is_completed = not todo.is_completed
        db.session.commit()
        flash('Task updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating task.', 'error')
    
    return redirect(url_for('employee_todos'))

@app.route('/employee/todos/<int:todo_id>/delete')
@login_required(role='employee')
def employee_todo_delete(todo_id):
    current_user = get_current_user()
    todo = Todo.query.filter_by(id=todo_id, employee_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(todo)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting task.', 'error')
    
    return redirect(url_for('employee_todos'))

# Employee Admin Messages Routes
@app.route('/employee/admin-messages')
@login_required(role='employee')
def employee_admin_messages():
    current_user = get_current_user()
    messages = AdminMessage.query.filter_by(sender_id=current_user.id).order_by(AdminMessage.created_at.desc()).all()
    return render_template('employee_admin_messages.html', messages=messages, current_user=current_user)

@app.route('/employee/admin-messages/send', methods=['GET', 'POST'])
@login_required(role='employee')
def employee_admin_messages_send():
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            subject = request.form.get('subject')
            content = request.form.get('content')
            
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
            flash('Error sending message to admin.', 'error')
    
    return render_template('employee_admin_messages_send.html', current_user=current_user)

# Admin Dashboard Routes
@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    current_user = get_current_user()
    
    # Get admin statistics
    total_employees = Employee.query.filter_by(is_active=True).count()
    pending_leave_requests = LeaveRequest.query.filter_by(status='pending').count()
    unread_admin_messages = AdminMessage.query.filter_by(is_read=False).count()
    active_employees = Employee.query.filter_by(is_active=True).count()
    
    # Get pending leave requests
    pending_leaves = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.created_at.desc()).limit(5).all()
    
    # Get recent admin messages
    recent_messages = AdminMessage.query.order_by(AdminMessage.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         total_employees=total_employees,
                         pending_leave_requests=pending_leave_requests,
                         unread_admin_messages=unread_admin_messages,
                         active_employees=active_employees,
                         pending_leaves=pending_leaves,
                         recent_messages=recent_messages,
                         current_user=current_user)

# Admin Employees Routes
@app.route('/admin/employees')
@login_required(role='admin')
def admin_employees():
    current_user = get_current_user()
    employees = Employee.query.order_by(Employee.created_at.desc()).all()
    return render_template('admin_employees.html', employees=employees, current_user=current_user)

@app.route('/admin/employees/add', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_employees_add():
    current_user = get_current_user()
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')
            phone = request.form.get('phone')
            department = request.form.get('department')
            position = request.form.get('position')
            hire_date_str = request.form.get('hire_date')
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else date.today()
            
            employee = Employee(
                email=email,
                password=generate_password_hash(password),
                name=name,
                phone=phone,
                department=department,
                position=position,
                hire_date=hire_date
            )
            
            db.session.add(employee)
            db.session.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('admin_employees'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding employee.', 'error')
    
    return render_template('admin_employees_add.html', current_user=current_user)

@app.route('/admin/employees/<int:employee_id>/toggle-status')
@login_required(role='admin')
def admin_employee_toggle_status(employee_id):
    current_user = get_current_user()
    employee = Employee.query.get_or_404(employee_id)
    
    try:
        employee.is_active = not employee.is_active
        db.session.commit()
        status = "activated" if employee.is_active else "deactivated"
        flash(f'Employee {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating employee status.', 'error')
    
    return redirect(url_for('admin_employees'))

@app.route('/admin/employees/<int:employee_id>/delete')
@login_required(role='admin')
def admin_employee_delete(employee_id):
    current_user = get_current_user()
    employee = Employee.query.get_or_404(employee_id)
    
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting employee.', 'error')
    
    return redirect(url_for('admin_employees'))

# Admin Leave Requests Routes
@app.route('/admin/leave-requests')
@login_required(role='admin')
def admin_leave_requests():
    current_user = get_current_user()
    leave_requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin_leave_requests.html', leave_requests=leave_requests, current_user=current_user)

@app.route('/admin/leave-requests/<int:request_id>/update')
@login_required(role='admin')
def admin_leave_request_update(request_id):
    current_user = get_current_user()
    leave_request = LeaveRequest.query.get_or_404(request_id)
    status = request.args.get('status')
    
    if status in ['approved', 'rejected']:
        try:
            leave_request.status = status
            leave_request.admin_notes = request.args.get('notes', '')
            db.session.commit()
            flash(f'Leave request {status} successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating leave request.', 'error')
    
    return redirect(url_for('admin_leave_requests'))

# Admin Messages Routes
@app.route('/admin/messages')
@login_required(role='admin')
def admin_messages():
    current_user = get_current_user()
    messages = AdminMessage.query.order_by(AdminMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages, current_user=current_user)

@app.route('/admin/messages/<int:message_id>/respond', methods=['POST'])
@login_required(role='admin')
def admin_message_respond(message_id):
    current_user = get_current_user()
    message = AdminMessage.query.get_or_404(message_id)
    
    try:
        message.admin_response = request.form.get('response')
        message.is_read = True
        db.session.commit()
        flash('Response sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error sending response.', 'error')
    
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:message_id>/mark-read')
@login_required(role='admin')
def admin_message_mark_read(message_id):
    current_user = get_current_user()
    message = AdminMessage.query.get_or_404(message_id)
    
    try:
        message.is_read = True
        db.session.commit()
        flash('Message marked as read!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating message.', 'error')
    
    return redirect(url_for('admin_messages'))

# Profile Route
@app.route('/profile')
@login_required()
def profile():
    current_user = get_current_user()
    if session.get('user_role') == 'admin':
        employees_count = Employee.query.filter_by(is_active=True).count()
        pending_leaves_count = LeaveRequest.query.filter_by(status='pending').count()
        return render_template('profile.html', 
                             employees_count=employees_count,
                             pending_leaves_count=pending_leaves_count,
                             current_user=current_user)
    else:
        return render_template('profile.html', current_user=current_user)

@app.route('/profile/update', methods=['POST'])
@login_required()
def update_profile():
    current_user = get_current_user()
    try:
        current_user.name = request.form.get('name')
        
        if session.get('user_role') == 'employee':
            current_user.phone = request.form.get('phone')
        
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password == confirm_password:
                current_user.password = generate_password_hash(new_password)
                flash('Password updated successfully!', 'success')
            else:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('profile'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile.', 'error')
    
    return redirect(url_for('profile'))

# Quick access routes (for development)
@app.route('/admin/quick')
def admin_quick_access():
    """Quick admin access for development"""
    secret_word = "maxelo"
    provided_word = request.args.get('key', '')
    
    if provided_word != secret_word:
        flash('Invalid access key', 'error')
        return redirect(url_for('admin_login'))
    
    admin = Admin.query.filter_by(email='admin@maxelo.co.za').first()
    if not admin:
        admin = Admin(
            email='admin@maxelo.co.za',
            password=generate_password_hash('admin123'),
            name='System Administrator'
        )
        db.session.add(admin)
        db.session.commit()
    
    session.clear()
    session['user_id'] = admin.id
    session['user_role'] = 'admin'
    session['user_name'] = admin.name
    session['user_email'] = admin.email
    session.permanent = True
    session.modified = True
    
    admin.last_login = datetime.utcnow()
    db.session.commit()
    
    flash('Quick admin access granted! Welcome back.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/employee/quick')
def employee_quick_access():
    """Quick employee access for development"""
    secret_word = "employee123"
    provided_word = request.args.get('key', '')
    
    if provided_word != secret_word:
        flash('Invalid access key', 'error')
        return redirect(url_for('employee_login'))
    
    employee = Employee.query.filter_by(email='mavis@maxelo.com').first()
    if not employee:
        employee = Employee(
            email='mavis@maxelo.com',
            password=generate_password_hash('123admin'),
            name='Mavis',
            department='Operations',
            position='Staff',
            hire_date=date.today()
        )
        db.session.add(employee)
        db.session.commit()
    
    session.clear()
    session['user_id'] = employee.id
    session['user_role'] = 'employee'
    session['user_name'] = employee.name
    session['user_email'] = employee.email
    session.permanent = True
    session.modified = True
    
    employee.last_login = datetime.utcnow()
    db.session.commit()
    
    flash('Quick employee access granted! Welcome back.', 'success')
    return redirect(url_for('employee_dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)