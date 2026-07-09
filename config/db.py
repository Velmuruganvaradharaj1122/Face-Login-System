import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = SQLAlchemy()

def init_app(app):
    """
    Initialize the database connection with the Flask application.
    """
    # Build Database URI from environment variables
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'password')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'face_login_db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
