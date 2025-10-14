from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Admin(BaseModel):
    """Admin user model"""
    __tablename__ = 'admins'
    
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    assigned_todos = db.relationship('AdminAssignedTodo', backref='admin', lazy=True)
    uploaded_documents = db.relationship('Document', backref='admin', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f'<Admin {self.email}>'

class Employee(BaseModel):
    """Employee user model"""
    __tablename__ = 'employees'
    
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Relationships
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    todos = db.relationship('Todo', backref='employee', lazy=True)
    documents = db.relationship('Document', backref='employee', lazy=True)
    admin_messages = db.relationship('AdminMessage', backref='sender', lazy=True)
    assigned_admin_todos = db.relationship('AdminAssignedTodo', backref='employee', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'position': self.position,
            'phone': self.phone,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<Employee {self.email}>'

class LeaveRequest(BaseModel):
    """Leave request model"""
    __tablename__ = 'leave_requests'
    
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    leave_type = db.Column(db.String(50), nullable=False)  # sick, vacation, personal, etc.
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    
    def get_duration(self):
        """Calculate leave duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'employee_name': self.employee.name if self.employee else None,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'reason': self.reason,
            'status': self.status,
            'duration': self.get_duration(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<LeaveRequest {self.leave_type} - {self.status}>'

class Message(BaseModel):
    """Internal messaging system between employees"""
    __tablename__ = 'messages'
    
    sender_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    
    # Relationships
    documents = db.relationship('MessageDocument', backref='message', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sender_name': self.sender.name if self.sender else None,
            'receiver_name': self.receiver.name if self.receiver else None,
            'subject': self.subject,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.subject}>'

class Todo(BaseModel):
    """Todo items for employees"""
    __tablename__ = 'todos'
    
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.Date, index=True)
    is_completed = db.Column(db.Boolean, default=False, index=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Todo {self.content[:50]}...>'

class Document(BaseModel):
    """Document storage model"""
    __tablename__ = 'documents'
    
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # Size in bytes
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50), default='other')
    tags = db.Column(db.String(200))
    is_important = db.Column(db.Boolean, default=False)
    uploaded_by_admin = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'description': self.description,
            'document_type': self.document_type,
            'is_important': self.is_important,
            'uploaded_by_admin': self.uploaded_by_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class AdminMessage(BaseModel):
    """Messages from employees to admin"""
    __tablename__ = 'admin_messages'
    
    sender_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    admin_response = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, index=True)
    
    # Relationships
    documents = db.relationship('AdminMessageDocument', backref='admin_message', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sender_name': self.sender.name if self.sender else None,
            'subject': self.subject,
            'content': self.content,
            'admin_response': self.admin_response,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AdminMessage {self.subject}>'

class Announcement(BaseModel):
    """System announcements"""
    __tablename__ = 'announcements'
    
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    publish_date = db.Column(db.Date, default=datetime.utcnow)
    expiry_date = db.Column(db.Date)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_active': self.is_active,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None
        }
    
    def __repr__(self):
        return f'<Announcement {self.title}>'

class MessageDocument(BaseModel):
    """Documents attached to messages"""
    __tablename__ = 'message_documents'
    
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    
    def __repr__(self):
        return f'<MessageDocument message:{self.message_id} doc:{self.document_id}>'

class AdminMessageDocument(BaseModel):
    """Documents attached to admin messages"""
    __tablename__ = 'admin_message_documents'
    
    admin_message_id = db.Column(db.Integer, db.ForeignKey('admin_messages.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    
    def __repr__(self):
        return f'<AdminMessageDocument admin_message:{self.admin_message_id} doc:{self.document_id}>'

class AdminAssignedTodo(BaseModel):
    """Todos assigned by admin to employees"""
    __tablename__ = 'admin_assigned_todos'
    
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    due_date = db.Column(db.Date, index=True)
    is_completed = db.Column(db.Boolean, default=False, index=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'admin_name': self.admin.name if self.admin else None,
            'employee_name': self.employee.name if self.employee else None,
            'content': self.content,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AdminAssignedTodo {self.content[:50]}...>'

# Database indexes for better performance
def create_indexes():
    """Create additional database indexes for performance"""
    # These would be created via migrations in a production environment
    pass