import os
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config.db import init_app, db
from face.register_face import process_registration
from face.recognize_face import process_login
from auth import (set_user_session, set_admin_session,
                  clear_user_session, clear_admin_session,
                  user_required, admin_required)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-change-in-production')

init_app(app)

# Separate session cookies for Admin and User servers so they don't share logins
SERVER_MODE = os.getenv('SERVER_MODE', 'all')
app.config['SESSION_COOKIE_NAME'] = f"face_login_session_{SERVER_MODE}"

from models.download_models import download_models
download_models()

with app.app_context():
    from models.user      import User
    from models.login_log import LoginLog
    from models.group     import Group, GroupMember
    from models.licence   import Licence
    from models.active_session import ActiveSession
    from models.message   import Message
    db.create_all()

def get_machine_id():
    return str(uuid.getnode())

# ═══════════════════════════════════════════════════════════════
#  SERVER MODE  —  read by run_admin.py / run_user.py
#  'admin' → only admin routes active, user /login returns 404
#  'user'  → only face login + dashboard active
#  unset   → all routes active (dev / original behaviour)
# ═══════════════════════════════════════════════════════════════

SERVER_MODE = os.getenv('SERVER_MODE', 'all')   # 'admin' | 'user' | 'all'

@app.context_processor
def inject_server_mode():
    return dict(server_mode=SERVER_MODE)

def admin_mode_only(f):
    """Block this route when running in user-only mode."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if SERVER_MODE == 'user':
            from flask import abort
            abort(404)
        return f(*args, **kwargs)
    return decorated

def user_mode_only(f):
    """Block this route when running in admin-only mode."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if SERVER_MODE == 'admin':
            from flask import abort
            abort(404)
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════
#  ENSURE ALL /api/* RESPONSES HAVE JSON CONTENT-TYPE
#  Prevents "Expecting value" JS crash when response body is valid
#  JSON but Content-Type header was not set correctly.
# ═══════════════════════════════════════════════════════════════

@app.after_request
def set_json_content_type(response):
    if request.path.startswith('/api/'):
        response.headers['Content-Type'] = 'application/json'
    return response

# ═══════════════════════════════════════════════════════════════
#  SESSION CLEANUP MIDDLEWARE
# ═══════════════════════════════════════════════════════════════
@app.before_request
def session_cleanup_middleware():
    """
    If a user is authenticated but their session key doesn't match the one in DB,
    clean it up. This prevents permanent lockouts if sessions get out of sync.
    """
    if 'user_id' in session and 'session_key' in session:
        from models.active_session import ActiveSession
        from auth import clear_user_session
        active = ActiveSession.query.filter_by(user_id=session['user_id']).first()
        # If there is no active session in DB, or the keys don't match, this browser's session is stale.
        if not active or active.session_key != session['session_key']:
            clear_user_session()


# ═══════════════════════════════════════════════════════════════
#  ROOT
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    if SERVER_MODE == 'admin':
        return redirect(url_for('admin_login_page'))
    return redirect(url_for('user_login_page'))


# ═══════════════════════════════════════════════════════════════
#  USER ROUTES  —  face login only
# ═══════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET'])
@user_mode_only
def user_login_page():
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
        
    from models.licence import Licence
    from datetime import datetime
    now = datetime.utcnow()
    
    # Check for active global licence
    # Assuming any active licence without users is a global licence
    is_expired = True
    expiry_date_str = "Unknown"
    
    active_licences = Licence.query.filter(
        Licence.is_active == True,
        Licence.valid_from <= now
    ).all()
    
    for lic in active_licences:
        if len(lic.users) == 0:
            if not lic.is_expired():
                is_expired = False
            else:
                expiry_date_str = lic.expires_at.strftime('%d %b %Y') if lic.expires_at else "Unknown"
            break

    return render_template('login.html', is_expired=is_expired, expiry_date_str=expiry_date_str)


@app.route('/dashboard')
@user_required
@user_mode_only
def user_dashboard():
    return render_template(
        'dashboard.html',
        user_name=session.get('user_full_name'),
        employee_id=session.get('user_employee_id')
    )

@app.route('/group-dashboard/<int:group_id>')
@user_required
@user_mode_only
def group_dashboard(group_id):
    from models.group import Group, GroupMember
    group = Group.query.get_or_404(group_id)
    
    # Verify user is in this group
    membership = GroupMember.query.filter_by(user_id=session['user_id'], group_id=group_id).first()
    if not membership:
        return redirect(url_for('user_dashboard'))
        
    return render_template('group_dashboard.html', group=group)

@app.route('/face-success/<int:group_id>')
@user_required
@user_mode_only
def face_success(group_id):
    from models.group import Group, GroupMember
    group = Group.query.get_or_404(group_id)
    
    # Verify user is in this group
    membership = GroupMember.query.filter_by(user_id=session['user_id'], group_id=group_id).first()
    if not membership:
        return redirect(url_for('user_dashboard'))
        
    # Get the plain password if it was set in the session right after creation
    # (Since it's no longer stored in DB, this will usually be None on login)
    plain_pass = session.pop(f'group_{group_id}_plain_password', None)
        
    return render_template('face_success.html', group=group, plain_pass=plain_pass)

@app.route('/logout')
@user_mode_only
def user_logout():
    if 'user_id' in session:
        from models.active_session import ActiveSession
        ActiveSession.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()
    clear_user_session()
    return redirect(url_for('user_login_page'))


# ═══════════════════════════════════════════════════════════════
#  ADMIN ROUTES  —  username + password, NO licence gate on login
# ═══════════════════════════════════════════════════════════════

@app.route('/admin_login', methods=['GET', 'POST'])
@admin_mode_only
def admin_login_page():
    """
    Admin login — always accessible, no licence check here.
    Licence is managed INSIDE the admin area after login.
    """
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        employee_id = request.form.get('employee_id', '').strip()
        password    = request.form.get('password', '').strip()

        if not employee_id or not password:
            error = 'Employee ID/Email and password are required.'
        else:
            if employee_id == 'adminit@email.com' and password == 'password@1122':
                session['admin_id'] = -1
                session['admin_employee_id'] = 'adminit@email.com'
                session['admin_full_name'] = 'System Admin'
                session['admin_role'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Invalid credentials or insufficient privileges.'

    return render_template('admin_login.html', error=error)


@app.route('/admin/dashboard')
@admin_required
@admin_mode_only
def admin_dashboard():
    """
    Admin home — shows system stats + licence status banner.
    Licence is expired/missing → banner shown, but admin can still work.
    """
    from models.user      import User
    from models.login_log import LoginLog
    from models.licence   import Licence

    total_users  = User.query.filter_by(role='user').count()
    total_admins = User.query.filter_by(role='admin').count()
    total_logs   = LoginLog.query.count()
    success_logs = LoginLog.query.filter_by(status='SUCCESS').count()

    # Licence info for the dashboard banner
    lic = Licence.query.filter_by(is_active=True).order_by(Licence.id.desc()).first()

    return render_template(
        'admin_dashboard.html',
        admin_name=session.get('admin_full_name'),
        total_users=total_users,
        total_admins=total_admins,
        total_logs=total_logs,
        success_logs=success_logs,
        licence=lic
    )


@app.route('/admin/logout')
@admin_mode_only
def admin_logout():
    clear_admin_session()
    return redirect(url_for('admin_login_page'))


@app.route('/register', methods=['GET'])
@admin_required
@admin_mode_only
def register_page():
    return render_template('register.html')


@app.route('/logs')
@admin_required
@admin_mode_only
def logs_page():
    from models.login_log import LoginLog
    all_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).all()
    return render_template('logs.html', logs=all_logs)


@app.route('/api/logs/delete', methods=['POST'])
@admin_required
@admin_mode_only
def api_delete_logs():
    """Delete multiple logs by ID."""
    from models.login_log import LoginLog
    data = request.json or {}
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({"success": False, "message": "No logs selected for deletion."}), 400
        
    try:
        LoginLog.query.filter(LoginLog.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"success": True, "message": f"Successfully deleted {len(ids)} logs."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/admin/users')
@admin_required
@admin_mode_only
def admin_users_page():
    from models.user import User
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin_users.html', users=users)


@app.route('/master')
@admin_required
@admin_mode_only
def master_page():
    from models.group import Group, GroupMember
    from models.user import User
    from models.login_log import LoginLog
    
    groups = Group.query.all()
    
    # Count active sessions (for demo: logins within last 1 hour)
    from datetime import datetime, timedelta
    active_since = datetime.utcnow() - timedelta(hours=1)
    
    # Simple active count
    active_sessions = db.session.query(LoginLog.user_id).filter(LoginLog.status == 'SUCCESS', LoginLog.timestamp >= active_since).distinct().count()
    
    total_in_groups = GroupMember.query.count()
    
    # Get all users for dropdown
    all_users = User.query.all()
    
    return render_template('master.html', groups=groups, active_sessions=active_sessions, total_in_groups=total_in_groups, all_users=all_users)


@app.route('/admin/licence')
@admin_required
@admin_mode_only
def admin_licence_page():
    """
    Licence management page — admin only, accessible after login.
    Admin generates keys here and activates them.
    """
    from models.licence import Licence
    lic     = Licence.query.filter_by(is_active=True).order_by(Licence.id.desc()).first()
    history = Licence.query.order_by(Licence.created_at.desc()).limit(10).all()
    return render_template('admin_licence.html', licence=lic, history=history)


# ═══════════════════════════════════════════════════════════════
#  API — FILE UPLOADS
# ═══════════════════════════════════════════════════════════════

from werkzeug.utils import secure_filename
from flask import send_from_directory

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload', methods=['POST'])
@user_required
@user_mode_only
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
        
    if file:
        original_filename = secure_filename(file.filename)
        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        mimetype = file.content_type or ''
        msg_type = 'file'
        if mimetype.startswith('image/'): msg_type = 'image'
        elif mimetype.startswith('video/'): msg_type = 'video'
        
        return jsonify({
            'success': True,
            'url': f"/uploads/{unique_filename}",
            'name': original_filename,
            'size': os.path.getsize(file_path),
            'type': msg_type,
            'mimetype': mimetype
        }), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ═══════════════════════════════════════════════════════════════
#  API — FACE LOGIN
# ═══════════════════════════════════════════════════════════════

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    image_data_uri = data.get('image')
    if not image_data_uri:
        return jsonify({"success": False, "message": "Image is required"}), 400

    try:
        result = process_login(image_data_uri)
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    if result.get("success"):
        from models.user      import User
        from models.login_log import LoginLog

        user_info = result.get("user", {})
        user_id   = user_info.get('id')

        # SQLAlchemy 2.x compatible lookup
        matched_user = db.session.get(User, user_id) if user_id else None

        if matched_user is None:
            return jsonify({"success": False, "message": "User not found in database."}), 404

        if not matched_user.is_active:
            return jsonify({"success": False, "message": "Account has been deactivated. Please contact the administrator."}), 403

        # Verify active licence for this user
        from models.licence import Licence
        from datetime import datetime
        now = datetime.utcnow()
        has_licence = False
        
        active_licences = Licence.query.filter(
            Licence.is_active == True,
            Licence.valid_from <= now,
            (Licence.expires_at == None) | (Licence.expires_at > now)
        ).all()
        
        for lic in active_licences:
            if len(lic.users) == 0:
                # Global licence applies to everyone
                has_licence = True
                break
            if matched_user in lic.users:
                # User-specific licence applies to this user
                has_licence = True
                break
                
        # Always allow admins to login via Face so they don't get locked out
        if matched_user.is_admin():
            has_licence = True
            
        if not has_licence:
            return jsonify({"success": False, "message": "Access Denied: Your account does not have an active subscription/licence."}), 403

        # ───────────────────────────────────────────────
        # Block new tab/browser if ActiveSession exists
        # ───────────────────────────────────────────────
        from models.active_session import ActiveSession
        active = ActiveSession.query.filter_by(user_id=matched_user.id).first()
        if active:
            return jsonify({
                "success": False, 
                "message": "⚠️ You are already logged in from another tab or browser. Please log out first."
            }), 403

        try:
            set_user_session(matched_user)
            
            # Generate and store unique session key
            import uuid
            session_key = uuid.uuid4().hex
            session['session_key'] = session_key
            
            # Create new ActiveSession
            new_active = ActiveSession(user_id=matched_user.id, session_key=session_key)
            db.session.add(new_active)
            
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            db.session.add(LoginLog(status='SUCCESS', user_id=matched_user.id, ip_address=client_ip))
            db.session.commit()
            
            # Group checking logic
            from models.group import GroupMember
            membership = GroupMember.query.filter_by(user_id=matched_user.id).first()
            if membership and membership.group and membership.group.dashboard_url:
                redirect_url = membership.group.dashboard_url
            else:
                redirect_url = "/dashboard"
                
            return jsonify({
                "success":  True,
                "message":  "Login successful!",
                "redirect": redirect_url,
                "is_admin": False,
                "user": user_info
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Session error: {str(e)}"}), 500
    else:
        from models.login_log import LoginLog
        try:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            db.session.add(LoginLog(status='FAILED', user_id=None, ip_address=client_ip))
            db.session.commit()
        except Exception:
            db.session.rollback()
        resp = jsonify({"success": False, "message": result.get("message", "Face not recognised.")})
        resp.headers['Content-Type'] = 'application/json'
        return resp, 401


# ═══════════════════════════════════════════════════════════════
#  API — REGISTER
# ═══════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
@admin_required
@admin_mode_only
def api_register():
    data           = request.json
    employee_id    = data.get('employee_id')
    full_name      = data.get('full_name')
    email          = data.get('email')
    image_data_uri = data.get('image')

    if not all([employee_id, full_name, email, image_data_uri]):
        return jsonify({"success": False, "message": "All fields and image are required"}), 400

    result = process_registration(employee_id, full_name, email, image_data_uri)
    return jsonify(result), 201 if result["success"] else 400


# ═══════════════════════════════════════════════════════════════
#  API — GROUP MANAGEMENT (Used by master.html)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/groups', methods=['POST'])
@admin_required
@admin_mode_only
def create_group():
    data = request.json
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    dashboard_url = data.get('redirect_url')
    
    if not all([name, username, password]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
        
    from models.group import Group
    
    if Group.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists"}), 400
        
    new_group = Group(group_name=name, username=username, password=password, dashboard_url=dashboard_url)
    new_group.set_plain_password(password)
    
    db.session.add(new_group)
    db.session.commit()
    
    session[f'group_{new_group.id}_plain_password'] = password
    
    return jsonify({"success": True, "message": "Group created successfully!"})

@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
@admin_required
@admin_mode_only
def delete_group(group_id):
    from models.group import Group
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"success": False, "message": "Group not found"}), 404
        
    db.session.delete(group)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Group deleted successfully!"})

@app.route('/api/groups/<int:group_id>', methods=['PUT'])
@admin_required
@admin_mode_only
def update_group(group_id):
    from models.group import Group
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"success": False, "message": "Group not found"}), 404
        
    data = request.json
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    dashboard_url = data.get('redirect_url')
    
    if name:
        group.group_name = name
    if username:
        # Check if new username exists in another group
        existing = Group.query.filter_by(username=username).first()
        if existing and existing.id != group_id:
            return jsonify({"success": False, "message": "Username already taken by another group"}), 400
        group.username = username
    if password:
        from werkzeug.security import generate_password_hash
        group.password_hash = generate_password_hash(password)
        # We don't save plain password again for security, only hash
    
    # Allow clearing the dashboard url
    if 'redirect_url' in data:
        group.dashboard_url = dashboard_url
        
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Group updated successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error updating group: {str(e)}"}), 500

@app.route('/api/groups/<int:group_id>/members', methods=['POST'])
@admin_required
@admin_mode_only
def add_member(group_id):
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "User ID required"}), 400
        
    from models.group import GroupMember
    existing = GroupMember.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({"success": False, "message": "User already belongs to a group"}), 400
        
    new_member = GroupMember(group_id=group_id, user_id=user_id)
    db.session.add(new_member)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Member added successfully!"})

@app.route('/api/groups/<int:group_id>/status', methods=['GET'])
@user_required
@user_mode_only
def group_status(group_id):
    from models.group import Group, GroupMember
    from models.login_log import LoginLog
    from datetime import datetime, timedelta
    
    group = Group.query.get_or_404(group_id)
    members = GroupMember.query.filter_by(group_id=group_id).all()
    
    active_since = datetime.utcnow() - timedelta(minutes=30)
    
    status_data = []
    for member in members:
        recent_login = LoginLog.query.filter_by(user_id=member.user_id, status='SUCCESS').filter(LoginLog.timestamp >= active_since).order_by(LoginLog.timestamp.desc()).first()
        status_data.append({
            "id": member.user_id,
            "full_name": member.user.full_name,
            "employee_id": member.user.employee_id,
            "status": "Online" if recent_login else "Offline"
        })
        
    return jsonify({"success": True, "members": status_data})


# ═══════════════════════════════════════════════════════════════
#  API — LICENCE  (admin only — generate + activate)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/users/list', methods=['GET'])
@admin_required
@admin_mode_only
def api_users_list():
    """Fetch all users to populate the multi-select dropdown for licences."""
    from models.user import User
    users = User.query.filter_by(role='user').all()
    user_data = [{"id": u.id, "full_name": u.full_name, "employee_id": u.employee_id} for u in users]
    return jsonify({"success": True, "users": user_data}), 200

@app.route('/api/groups/list', methods=['GET'])
@admin_required
@admin_mode_only
def api_groups_list():
    """Fetch all groups to populate the multi-select dropdown for licences."""
    from models.group import Group
    groups = Group.query.all()
    group_data = [{"id": g.id, "group_name": g.group_name} for g in groups]
    return jsonify({"success": True, "groups": group_data}), 200

@app.route('/api/licence/generate', methods=['POST'])
@admin_required
@admin_mode_only
def api_generate_licence():
    """
    Generate a new product key. Admin calls this to create a key,
    which can then be activated immediately or saved for later.
    """
    from models.licence import Licence
    data       = request.json or {}
    machine_id = data.get('machine_id', 'GLOBAL').strip() or 'GLOBAL'
    year       = data.get('year', None)

    key = Licence.generate_key(machine_id=machine_id, year=year)
    return jsonify({"success": True, "product_key": key, "machine_id": machine_id}), 200


@app.route('/api/licence/activate', methods=['POST'])
@admin_required
@admin_mode_only
def api_activate_licence():
    """
    Activate a product key. Must be logged in as admin to call this.
    Validates format, deactivates old key, creates new 1-year licence.
    """
    from models.licence import Licence
    from datetime import datetime, timedelta

    data        = request.json or {}
    product_key = data.get('product_key', '').strip().upper()
    machine_id  = data.get('machine_id', 'GLOBAL').strip() or 'GLOBAL'
    valid_from_str = data.get('valid_from')
    expires_at_str = data.get('expires_at')
    user_ids    = data.get('user_ids', [])
    group_ids   = data.get('group_ids', [])

    if not product_key:
        return jsonify({"success": False, "message": "Product key is required."}), 400

    if not Licence.validate_key_format(product_key):
        return jsonify({"success": False,
                        "message": "Invalid key format. Expected XXXX-XXXX-XXXX-XXXX."}), 400

    # Parse custom dates if provided
    valid_from = datetime.utcnow()
    if valid_from_str:
        try:
            valid_from = datetime.fromisoformat(valid_from_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            pass

    expires_at = datetime.utcnow() + timedelta(days=365)
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            pass

    # Deactivate existing active licences
    for old in Licence.query.filter_by(is_active=True).all():
        old.is_active = False

    new_lic              = Licence(product_key=product_key, machine_id=machine_id)
    new_lic.is_active    = True
    new_lic.activated_at = datetime.utcnow()
    new_lic.valid_from   = valid_from
    new_lic.expires_at   = expires_at
    
    # Assign specific users if provided
    # Combine individual user IDs and users from selected groups
    final_user_ids = set(user_ids)
    
    if group_ids:
        from models.group import GroupMember
        group_members = GroupMember.query.filter(GroupMember.group_id.in_(group_ids)).all()
        for gm in group_members:
            final_user_ids.add(gm.user_id)
            
    if final_user_ids:
        from models.user import User
        users_to_assign = User.query.filter(User.id.in_(list(final_user_ids))).all()
        new_lic.users.extend(users_to_assign)

    db.session.add(new_lic)
    db.session.commit()

    return jsonify({
        "success":      True,
        "message":      "Licence activated successfully.",
        "product_key":  new_lic.product_key,
        "valid_from":   new_lic.valid_from.strftime('%d %b %Y'),
        "expires_at":   new_lic.expires_at.strftime('%d %b %Y'),
        "days_remaining": new_lic.days_remaining()
    }), 200


@app.route('/api/licence/revoke', methods=['POST'])
@admin_required
@admin_mode_only
def api_revoke_licence():
    """Deactivate the current licence (admin only)."""
    from models.licence import Licence
    for lic in Licence.query.filter_by(is_active=True).all():
        lic.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": "Licence revoked."}), 200


# ═══════════════════════════════════════════════════════════════
#  API — USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
@admin_mode_only
def api_update_user(user_id):
    from models.user import User
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    data = request.json
    user.full_name = data.get('full_name', user.full_name)
    user.employee_id = data.get('employee_id', user.employee_id)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    
    db.session.commit()
    return jsonify({"success": True, "message": "User updated successfully."}), 200

@app.route('/api/users/<int:user_id>/face', methods=['PUT'])
@admin_required
@admin_mode_only
def api_update_user_face(user_id):
    from models.user import User
    import base64
    import numpy as np
    import cv2
    import json
    from face.encoding import generate_face_encoding, serialize_encoding

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    data = request.json
    image_data_uri = data.get('image')
    if not image_data_uri:
        return jsonify({"success": False, "message": "No image data provided"}), 400

    try:
        if ',' in image_data_uri:
            image_data = image_data_uri.split(',')[1]
        else:
            image_data = image_data_uri
            
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        encoding = generate_face_encoding(img)
        if encoding is None:
            return jsonify({"success": False, "message": "No face detected in the image. Please try again."}), 400
            
        encoding_list = serialize_encoding(encoding)
        encoding_json = json.dumps(encoding_list)
        
        user.face_encoding = encoding_json
        db.session.commit()
        
        return jsonify({"success": True, "message": "Face registration updated successfully."}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to process face: {str(e)}"}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
@admin_mode_only
def api_delete_user(user_id):
    from models.user import User
    from models.login_log import LoginLog
    from models.group import GroupMember
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    # Hard delete: Clean up related records
    LoginLog.query.filter_by(user_id=user.id).delete()
    GroupMember.query.filter_by(user_id=user.id).delete()
    user.licences = [] # Clear Many-to-Many associations
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"success": True, "message": "User permanently deleted."}), 200


if __name__ == '__main__':
    import subprocess
    import sys
    
    print("=" * 50)
    print("  STARTING BOTH ADMIN AND USER SERVERS")
    print("=" * 50)
    
    # Start both servers in separate processes
    admin_process = subprocess.Popen([sys.executable, 'run_admin.py'])
    user_process = subprocess.Popen([sys.executable, 'run_user.py'])
    
    try:
        admin_process.wait()
        user_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down both servers...")
        admin_process.terminate()
        user_process.terminate()
