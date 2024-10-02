from flask import request, jsonify, Blueprint
from app import db, login_manager
from flask_login import login_user, logout_user, current_user
from models import User

@user_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        login_user(user)
        user.visits += 1
        db.session.commit()
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"error": "User not found"}), 404

@user_routes.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200
