from flask import Blueprint, request, jsonify
from models import db, User, UserRole
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from services.auth import hash_password, check_password, admin_required

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password(user.password, data['password']):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Generate tokens
    access_token = create_access_token(identity=user.username)
    refresh_token = create_refresh_token(identity=user.username)
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    })

@auth_bp.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    
    return jsonify({
        "access_token": access_token
    })

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(user.to_dict())

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.json
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({"error": "Current password and new password required"}), 400
        
    # Check current password
    if not check_password(user.password, data['current_password']):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    # Update password
    user.password = hash_password(data['new_password'])
    db.session.commit()
    
    return jsonify({"message": "Password changed successfully"})
