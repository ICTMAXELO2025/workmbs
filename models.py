# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# Set South Africa timezone
SAST = pytz.timezone('Africa/Johannesburg')

def get_sast_time():
    return datetime.now(SAST)

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date, default=lambda: get_sast_time().date())
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender_employee', lazy=True, cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver_employee', lazy=True, cascade='all, delete-orphan')
    todos = db.relationship('Todo', backref='employee', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='employee', lazy=True, cascade='all, delete-orphan')
    admin_messages = db.relationship('AdminMessage', backref='employee', lazy=True, cascade='all, delete-orphan')
    assigned_todos_rel = db.relationship('AdminAssignedTodo', backref='employee', lazy=True, cascade='all, delete-orphan')

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    last_login = db.Column(db.DateTime)
    
    # Relationships - FIXED: Removed problematic relationships
    uploaded_documents = db.relationship('Document', backref='admin', lazy=True, cascade='all, delete-orphan')
    assigned_todos = db.relationship('AdminAssignedTodo', backref='admin', lazy=True, cascade='all, delete-orphan')

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    updated_at = db.Column(db.DateTime, default=get_sast_time, onupdate=get_sast_time)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    
    # Relationships for message documents
    documents = db.relationship('MessageDocument', backref='message', lazy=True, cascade='all, delete-orphan')

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    is_completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    updated_at = db.Column(db.DateTime, default=get_sast_time, onupdate=get_sast_time)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'))  # If uploaded by admin
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50), default='other')
    tags = db.Column(db.String(200))
    is_important = db.Column(db.Boolean, default=False)
    uploaded_by_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_sast_time)

class AdminMessage(db.Model):
    __tablename__ = 'admin_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    admin_response = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    updated_at = db.Column(db.DateTime, default=get_sast_time, onupdate=get_sast_time)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=get_sast_time)

class MessageDocument(db.Model):
    __tablename__ = 'message_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=get_sast_time)

class AdminMessageDocument(db.Model):
    __tablename__ = 'admin_message_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_message_id = db.Column(db.Integer, db.ForeignKey('admin_messages.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=get_sast_time)

class AdminAssignedTodo(db.Model):
    __tablename__ = 'admin_assigned_todos'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='CASCADE'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    is_completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=get_sast_time)
    updated_at = db.Column(db.DateTime, default=get_sast_time, onupdate=get_sast_time)