import os
os.environ['SERVER_MODE'] = 'user'

from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("  USER SERVER  →  http://127.0.0.1:8000/login")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8000, debug=True)
