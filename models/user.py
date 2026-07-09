from config.db import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    User model for storing employee information and face encodings.
    role: 'admin' — can access admin_login, master control, logs, register
          'user'  — can only access /login (face recognition) and /dashboard
    """
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id   = db.Column(db.String(50),  unique=True, nullable=False)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(100), unique=True, nullable=False)
    face_encoding = db.Column(db.Text, nullable=False)
    # Role controls which login portal this user may access
    role          = db.Column(db.String(20), nullable=False, default='user')
    # Admin password hash — only populated for role='admin'
    password_hash = db.Column(db.String(255), nullable=True, default=None)
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, employee_id, full_name, email, face_encoding,
                 role='user', password=None, is_active=True):
        self.employee_id   = employee_id
        self.full_name     = full_name
        self.email         = email
        self.face_encoding = face_encoding
        self.role          = role
        self.is_active     = is_active
        if password:
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.full_name} ({self.employee_id}) role={self.role}>"
