from flask import Blueprint, request, jsonify
from models import db, User

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "description": u.description
        })
    return jsonify(result)

@users_bp.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    description = data.get('description', "")

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400
    
    new_user = User(username=username, description=description)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"})

@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"})
