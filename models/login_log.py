from config.db import db
from datetime import datetime

class LoginLog(db.Model):
    """
    Model for storing login attempts.
    """
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for failed unrecognized faces
    status = db.Column(db.String(20), nullable=False) # 'SUCCESS' or 'FAILED'
    ip_address = db.Column(db.String(45), nullable=True) # Supports IPv4 and IPv6
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user
    user = db.relationship('User', backref=db.backref('login_logs', lazy=True))

    def __init__(self, status, user_id=None, ip_address=None):
        self.status = status
        self.user_id = user_id
        self.ip_address = ip_address

    def __repr__(self):
        return f"<LoginLog {self.status} at {self.timestamp}>"
