from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sklearn.neighbors import NearestNeighbors
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

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    audience_segment = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes for user authentication
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        login_user(user)
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# Start and end interaction, awarding reward points
@app.route('/start_interaction', methods=['POST'])
@login_required
def start_interaction():
    session['start_time'] = datetime.now().isoformat()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
    return jsonify({"message": "Interaction started"}), 200

@app.route('/end_interaction', methods=['POST'])
@login_required
def end_interaction():
    start_time = session.pop('start_time', None)
    if start_time:
        end_time = datetime.now()
        duration = (end_time - datetime.fromisoformat(start_time)).total_seconds()
        current_user.reward_points += int(duration / 60)  # Award 1 point per minute
        db.session.commit()
        return jsonify({"message": "Interaction ended", "reward_points": current_user.reward_points}), 200
    return jsonify({"error": "No active interaction found"}), 404

# Room booking and release routes
@app.route('/rooms/<int:room_id>/book', methods=['POST'])
@login_required
def book_room(room_id):
    room = Room.query.get(room_id)
    if room and room.available:
        data = request.get_json()
        try:
            check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        if check_in >= check_out:
            return jsonify({"error": "Check-out must be after check-in"}), 400

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

# Subscription route with email validation
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data.get('email')
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
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

# Get all events
@app.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([{ 'name': event.name, 'date': event.date.strftime('%Y-%m-%d'), 'location': event.location, 'category': event.category } for event in events])

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

    if not user.preferences:
        return jsonify({"message": "No user preferences found"}), 200

    user_preferences = user.preferences.split(',')
    events = Event.query.all()
    recommended_events = [event for event in events if event.category in user_preferences]
    
    return jsonify([{ 'name': event.name, 'date': event.date.strftime('%Y-%m-%d'), 'location': event.location, 'category': event.category } for event in recommended_events])

# Campaigns management route
@app.route('/campaigns', methods=['POST'])
@login_required
def create_campaign():
    data = request.get_json()
    campaign = Campaign(name=data['name'], content=data['content'], audience_segment=data['audience_segment'])
    db.session.add(campaign)
    db.session.commit()
    return jsonify({"message": "Campaign created successfully"}), 200

# Get all campaigns
@app.route('/campaigns', methods=['GET'])
def get_campaigns():
    campaigns = Campaign.query.all()
    return jsonify([{ 'name': campaign.name, 'content': campaign.content, 'audience_segment': campaign.audience_segment, 'created_at': campaign.created_at.strftime('%Y-%m-%d %H:%M:%S') } for campaign in campaigns])

# Graceful shutdown of the scheduler
@app.before_first_request
def before_first_request():
    db.create_all()
    scheduler.start()

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
