from config.db import db
from datetime import datetime

class License(db.Model):
    __tablename__ = 'licenses'

    id = db.Column(db.Integer, primary_key=True)
    product_key = db.Column(db.String(100), unique=True, nullable=False)
    machine_id = db.Column(db.String(255), nullable=False)
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_valid(self):
        return datetime.utcnow() <= self.expires_at
