from flask import request, jsonify, Blueprint
from app import db, login_manager
from flask_login import login_user, logout_user, current_user, login_required
from models import User
from werkzeug.security import check_password_hash, generate_password_hash
from utils.validation import validate_user_data
import datetime  # Import datetime for timestamps

# Blueprint for user-related routes
user_routes = Blueprint('user_routes', __name__)

# Login endpoint
@user_routes.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            user.visits += 1
            user.last_login = datetime.datetime.now() # Update last login time
            db.session.commit()
            return jsonify({"message": "Logged in successfully", "user": {"email": user.email, "visits": user.visits, "last_login": user.last_login}}), 200

        return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Logout endpoint
@user_routes.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Protected endpoint to check the current user's details
@user_routes.route('/current_user', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        "email": current_user.email,
        "visits": current_user.visits,
        "reward_points": current_user.reward_points,
        "last_login": current_user.last_login # Include last login time
    }), 200

# Register endpoint
@user_routes.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        validation_error = validate_user_data(data)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        email = data.get('email')
        password = data.get('password')

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User with this email already exists"}), 400

        new_user = User(
            email=email,
            password=generate_password_hash(password),
            reward_points=0,
            visits=0,
            registration_date=datetime.datetime.now() # Add registration date
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
