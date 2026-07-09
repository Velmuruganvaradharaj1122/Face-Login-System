"""
auth.py — Session helpers and route decorators.

Two separate session namespaces:
  session['user_*']  — set after face login  → gates /dashboard
  session['admin_*'] — set after admin login → gates /admin/* routes

This means a user session and admin session can coexist independently,
and clearing one does not affect the other.
"""
from functools import wraps
from flask import session, redirect, url_for, request


# ─────────────────────────────────────────────
#  Session writers
# ─────────────────────────────────────────────

def set_user_session(user):
    """Called after a successful face login."""
    session['user_id']          = user.id
    session['user_full_name']   = user.full_name
    session['user_employee_id'] = user.employee_id
    session['user_email']       = user.email
    session['user_role']        = user.role


def set_admin_session(user):
    """Called after a successful admin username/password login."""
    session['admin_id']          = user.id
    session['admin_full_name']   = user.full_name
    session['admin_employee_id'] = user.employee_id
    session['admin_email']       = user.email


def clear_user_session():
    for key in ['user_id', 'user_full_name', 'user_employee_id',
                'user_email', 'user_role']:
        session.pop(key, None)


def clear_admin_session():
    for key in ['admin_id', 'admin_full_name', 'admin_employee_id',
                'admin_email']:
        session.pop(key, None)


# ─────────────────────────────────────────────
#  Decorators
# ─────────────────────────────────────────────

def user_required(f):
    """
    Protects user-only routes (/dashboard).
    Redirects to /login if no active user session.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('user_login_page'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """
    Protects admin-only routes (/admin/*, /logs, /register, /master).
    Redirects to /admin_login if no active admin session.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated
