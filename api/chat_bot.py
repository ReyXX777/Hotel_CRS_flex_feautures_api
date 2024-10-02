from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import numpy as np
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
scheduler = BackgroundScheduler()

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    preferences = db.Column(db.String(500), nullable=True)  # JSON string of user preferences
    reward_points = db.Column(db.Integer, default=0)
    visits = db.Column(db.Integer, default=0)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    room = db.relationship('Room', backref=db.backref('reviews', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Authentication Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        login_user(user)
        user.visits += 1
        db.session.commit()
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# Room and Event Booking System
@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in rooms])

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = Room.query.get(room_id)
    if room:
        return jsonify({ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available })
    return jsonify({"error": "Room not found"}), 404

@app.route('/rooms/<int:room_id>/book', methods=['POST'])
@login_required
def book_room(room_id):
    room = Room.query.get(room_id)
    if room and room.available:
        data = request.get_json()
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        booking = Booking(user_id=current_user.id, room_id=room_id, check_in=check_in, check_out=check_out)
        room.available = False
        current_user.reward_points += 100  # Award 100 points per booking
        db.session.add(booking)
        db.session.commit()
        return jsonify({"message": f"Room {room_id} booked successfully"}), 200
    return jsonify({"error": "Room not available or not found"}), 400

@app.route('/rooms/<int:room_id>/release', methods=['POST'])
@login_required
def release_room(room_id):
    room = Room.query.get(room_id)
    if room and not room.available:
        room.available = True
        db.session.commit()
        return jsonify({"message": f"Room {room_id} released successfully"}), 200
    return jsonify({"error": "Room not booked or not found"}), 400

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data['email']
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email address"}), 400

    if not User.query.filter_by(email=email).first():
        user = User(email=email)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Subscribed successfully"}), 200
    return jsonify({"error": "Already subscribed"}), 400

# Add events
@app.route('/events', methods=['POST'])
@login_required
def add_event():
    data = request.get_json()
    event = Event(name=data['name'], date=datetime.strptime(data['date'], '%Y-%m-%d'), location=data['location'], category=data['category'])
    db.session.add(event)
    db.session.commit()
    return jsonify({"message": "Event added successfully"}), 200

# Room recommendations based on user preferences and bookings
@app.route('/recommendations/rooms/<int:user_id>', methods=['GET'])
@login_required
def recommend_rooms(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_bookings = Booking.query.filter_by(user_id=user_id).all()
    if not user_bookings:
        return jsonify({"message": "No previous bookings found"}), 200

    room_ids = [booking.room_id for booking in user_bookings]
    room_types = [Room.query.get(room_id).room_type for room_id in room_ids]
    preferred_room_type = max(set(room_types), key=room_types.count)

    recommended_rooms = Room.query.filter_by(room_type=preferred_room_type, available=True).all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in recommended_rooms])

# Event recommendations based on user preferences
@app.route('/recommendations/events/<int:user_id>', methods=['GET'])
@login_required
def recommend_events(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_preferences = user.preferences
    if not user_preferences:
        return jsonify({"message": "No user preferences found"}), 200

    user_preferences = user_preferences.split(',')
    events = Event.query.all()
    recommended_events = [event for event in events if event.category in user_preferences]

    return jsonify([{ 'name': event.name, 'date': event.date.strftime('%Y-%m-%d'), 'location': event.location, 'category': event.category } for event in recommended_events])

# Add Review functionality
@app.route('/rooms/<int:room_id>/review', methods=['POST'])
@login_required
def add_review(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    data = request.get_json()
    rating = data.get('rating')
    comment
