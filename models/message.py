from config.db import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Use receiver_id for 1-to-1 chat, OR group_id for group chat
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    group_id = db.Column(db.Integer, db.ForeignKey('groups_tbl.id'), nullable=True)
    
    type = db.Column(db.String(20), default='text') # 'text', 'file', 'image', 'video'
    content = db.Column(db.Text, nullable=False)    # Text message OR file URL
    file_name = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    group = db.relationship('Group', foreign_keys=[group_id])
