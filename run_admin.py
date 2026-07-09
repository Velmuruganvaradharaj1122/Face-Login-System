import os
os.environ['SERVER_MODE'] = 'admin'

from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("  ADMIN SERVER  →  http://127.0.0.1:5000/admin_login")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
