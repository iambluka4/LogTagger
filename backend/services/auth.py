from flask import request, jsonify
from functools import wraps
from flask_jwt_extended import (
    get_jwt_identity, verify_jwt_in_request, 
    create_access_token, create_refresh_token
)
import bcrypt
from datetime import datetime, timedelta
from models import User, UserRole, db

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed, password):
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def admin_required(fn):
    """Decorator to require admin role for an endpoint"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify(message="Admin access required"), 403
        
        return fn(*args, **kwargs)
    return wrapper

def analyst_required(fn):
    """Decorator to require analyst or admin role for an endpoint"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        
        if not user or (user.role != UserRole.ANALYST and user.role != UserRole.ADMIN):
            return jsonify(message="Analyst access required"), 403
        
        return fn(*args, **kwargs)
    return wrapper

def login_user(username, password):
    """Login a user and generate JWT tokens"""
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password(user.password, password):
        return None, None
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(
        identity=username, 
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity=username,
        expires_delta=timedelta(days=30)
    )
    
    return access_token, refresh_token

def create_admin_if_not_exists():
    """Create default admin user if no admin exists"""
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    
    if not admin:
        admin = User(
            username="admin",
            password=hash_password("admin"),  # This should be changed immediately
            description="Default administrator account",
            role=UserRole.ADMIN
        )
        db.session.add(admin)
        db.session.commit()
        return True
    
    return False
