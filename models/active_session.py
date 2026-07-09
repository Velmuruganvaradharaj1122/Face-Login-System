from config.db import db
from datetime import datetime

class ActiveSession(db.Model):
    """
    Model to track active user sessions and enforce single-device login.
    """
    __tablename__ = 'active_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    session_key = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user
    user = db.relationship('User', backref=db.backref('active_session', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<ActiveSession User:{self.user_id} Key:{self.session_key}>"
