from config.db import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Group(db.Model):
    """
    Group model — stores a named group with shared login credentials.
    Multiple employees (GroupMember rows) belong to one group.
    They all share the same username/password to access the group dashboard.
    """
    __tablename__ = 'groups_tbl'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name    = db.Column(db.String(100), unique=True, nullable=False)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    dashboard_url = db.Column(db.String(255), default=None)
    is_active     = db.Column(db.Boolean, default=True)
    created_by    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), default=None)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: all members that belong to this group
    members = db.relationship('GroupMember', backref='group', cascade='all, delete-orphan', lazy=True)

    def __init__(self, group_name, username, password, dashboard_url=None, created_by=None):
        self.group_name    = group_name
        self.username      = username
        self.password_hash = generate_password_hash(password)
        self.dashboard_url = dashboard_url
        self.created_by    = created_by

    def check_password(self, password):
        """Verify a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_plain_password(self):
        """
        Returns the plain-text password for display on the face-success screen.
        Stored separately in the session after face auth — never exposed via API
        without a successful face match first.
        """
        # Plain password is NOT stored — set it via set_plain_password() at creation
        return getattr(self, '_plain_password', None)

    def set_plain_password(self, password):
        """
        Call this right after creating a Group to temporarily hold the plain
        password so it can be shown once on the master control page.
        This is NOT persisted — it lives only in the current request context.
        """
        self._plain_password = password
        self.password_hash = generate_password_hash(password)

    def to_dict(self, include_members=False):
        data = {
            'id':           self.id,
            'group_name':   self.group_name,
            'username':     self.username,
            'dashboard_url': self.dashboard_url,
            'is_active':    self.is_active,
            'created_at':   self.created_at.isoformat() if self.created_at else None,
        }
        if include_members:
            data['members'] = [m.to_dict() for m in self.members]
        return data

    def __repr__(self):
        return f"<Group {self.group_name} ({self.username})>"


class GroupMember(db.Model):
    """
    GroupMember model — links one user to one group.
    A user can belong to only one group (user_id is UNIQUE).
    """
    __tablename__ = 'group_members'

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id  = db.Column(db.Integer, db.ForeignKey('groups_tbl.id', ondelete='CASCADE'), nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id',       ondelete='CASCADE'), nullable=False, unique=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Easy access back to the user record
    user = db.relationship('User', backref=db.backref('group_membership', uselist=False))

    def __init__(self, group_id, user_id):
        self.group_id = group_id
        self.user_id  = user_id

    def to_dict(self):
        return {
            'id':        self.id,
            'group_id':  self.group_id,
            'user_id':   self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'user': {
                'employee_id': self.user.employee_id,
                'full_name':   self.user.full_name,
                'email':       self.user.email,
            } if self.user else None,
        }

    def __repr__(self):
        return f"<GroupMember user_id={self.user_id} group_id={self.group_id}>"
