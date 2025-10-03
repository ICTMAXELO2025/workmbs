from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password"""
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f'<Admin {self.email}>'

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True, cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='employee', lazy=True, cascade='all, delete-orphan')
    todos = db.relationship('Todo', backref='employee', lazy=True, cascade='all, delete-orphan')
    admin_messages = db.relationship('AdminMessage', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password"""
        return check_password_hash(self.password, password)
    
    def get_pending_leaves_count(self):
        """Get count of pending leave requests"""
        return len([lr for lr in self.leave_requests if lr.status == 'pending'])
    
    def get_unread_messages_count(self):
        """Get count of unread messages"""
        return len([msg for msg in self.received_messages if not msg.is_read])
    
    def __repr__(self):
        return f'<Employee {self.email}>'

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_duration(self):
        """Calculate leave duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def is_pending(self):
        """Check if leave request is pending"""
        return self.status == 'pending'
    
    def __repr__(self):
        return f'<LeaveRequest {self.leave_type} - {self.status}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.updated_at = datetime.utcnow()
    
    def get_preview(self, length=100):
        """Get preview of message content"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'
    
    def __repr__(self):
        return f'<Message {self.subject}>'

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_file_size_display(self):
        """Get human readable file size"""
        if self.file_size is None:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='medium')
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def toggle_complete(self):
        """Toggle completion status"""
        self.is_completed = not self.is_completed
        self.updated_at = datetime.utcnow()
    
    def is_overdue(self):
        """Check if todo is overdue"""
        if self.due_date and not self.is_completed:
            return self.due_date < date.today()
        return False
    
    def get_priority_class(self):
        """Get CSS class for priority"""
        priority_classes = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'info'
        }
        return priority_classes.get(self.priority, 'secondary')
    
    def __repr__(self):
        return f'<Todo {self.content[:50]}>'

class AdminMessage(db.Model):
    __tablename__ = 'admin_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def mark_as_read(self):
        """Mark message as read by admin"""
        self.is_read = True
        self.updated_at = datetime.utcnow()
    
    def has_response(self):
        """Check if admin has responded"""
        return self.admin_response is not None and self.admin_response.strip() != ''
    
    def get_preview(self, length=100):
        """Get preview of message content"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'
    
    def __repr__(self):
        return f'<AdminMessage {self.subject}>'