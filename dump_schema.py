import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
cnx = mysql.connector.connect(
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '3306'),
    database=os.getenv('DB_NAME', 'face_login_db')
)

cursor = cnx.cursor()
cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    cursor.execute(f"SHOW CREATE TABLE {table}")
    print(f"-- Table: {table}")
    print(cursor.fetchone()[1])
    print(";")
    print()
cnx.close()
