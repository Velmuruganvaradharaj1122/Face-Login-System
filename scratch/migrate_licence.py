import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from config.db import db
from models.licence import Licence, licence_users

with app.app_context():
    print("Dropping old licence table...")
    db.session.execute(db.text("DROP TABLE IF EXISTS licence_users;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS licence;"))
    db.session.commit()
    
    print("Creating new licence tables...")
    db.create_all()
    print("Done!")
