from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Employee(db.Model):
    __tablename__ = 'employee'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class LeaveRequest(db.Model):
    __tablename__ = 'leave_request'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee', backref=db.backref('leave_requests', lazy=True))

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sender = db.relationship('Employee', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    receiver = db.relationship('Employee', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy=True))
    
    # Relationship for attached documents in regular messages
    attached_documents = db.relationship('MessageDocument', backref='message', lazy=True, cascade='all, delete-orphan')

class Document(db.Model):
    __tablename__ = 'document'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50), default='other')  # contract, policy, hr, payslip, training, other
    tags = db.Column(db.String(200))  # comma-separated tags
    is_important = db.Column(db.Boolean, default=False)
    uploaded_by_admin = db.Column(db.Boolean, default=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)  # if uploaded by admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('documents', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('uploaded_documents', lazy=True))

class Todo(db.Model):
    __tablename__ = 'todo'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('todos', lazy=True))

class AdminMessage(db.Model):
    __tablename__ = 'admin_message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    admin_response = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sender = db.relationship('Employee', backref=db.backref('admin_messages', lazy=True))
    
    # Relationship for attached documents in admin messages
    attached_documents = db.relationship('AdminMessageDocument', backref='admin_message', lazy=True, cascade='all, delete-orphan')

class MessageDocument(db.Model):
    __tablename__ = 'message_document'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminMessageDocument(db.Model):
    __tablename__ = 'admin_message_document'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_message_id = db.Column(db.Integer, db.ForeignKey('admin_message.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Model for admin-created todos assigned to employees
class AdminAssignedTodo(db.Model):
    __tablename__ = 'admin_assigned_todo'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('Admin', backref=db.backref('assigned_todos', lazy=True))
    employee = db.relationship('Employee', backref=db.backref('assigned_todos', lazy=True))

# Model for system announcements/broadcasts
class Announcement(db.Model):
    __tablename__ = 'announcement'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    admin = db.relationship('Admin', backref=db.backref('announcements', lazy=True))

# Model for tracking document downloads/access
class DocumentAccessLog(db.Model):
    __tablename__ = 'document_access_log'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    # Relationships
    document = db.relationship('Document', backref=db.backref('access_logs', lazy=True))
    employee = db.relationship('Employee', backref=db.backref('document_accesses', lazy=True))

# Model for notification system
class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, warning, success, error
    is_read = db.Column(db.Boolean, default=False)
    related_url = db.Column(db.String(500))  # URL for the notification action
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = db.relationship('Employee', backref=db.backref('notifications', lazy=True))