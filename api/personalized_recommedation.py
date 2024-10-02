from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
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

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    preferences = db.Column(db.String(500), nullable=True)  # JSON string of user preferences
    confirmed = db.Column(db.Boolean, default=False)  # Email confirmation

    def __repr__(self):
        return f"<User {self.email}>"

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

# Routes
@app.route('/')
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

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
            return jsonify({"error": "Check-out date must be after check-in"}), 400

        booking = Booking(user_id=data['user_id'], room_id=room_id, check_in=check_in, check_out=check_out)
        room.available = False
        db.session.add(booking)
        db.session.commit()
        return jsonify({"message": f"Room {room_id} booked successfully"}), 200
    return jsonify({"error": "Room not available or not found"}), 400

@app.route('/rooms/<int:room_id>/release', methods=['POST'])
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
    email = data.get('email')
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email address"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Already subscribed"}), 400

    user = User(email=email)
    db.session.add(user)
    db.session.commit()

    # Send confirmation email
    msg = Message('Confirm your subscription', recipients=[email])
    msg.body = 'Click the link to confirm your subscription.'
    mail.send(msg)

    return jsonify({"message": "Subscribed successfully, check your email for confirmation"}), 200

@app.route('/confirm/<int:user_id>', methods=['GET'])
def confirm_email(user_id):
    user = User.query.get(user_id)
    if user:
        user.confirmed = True
        db.session.commit()
        return jsonify({"message": "Email confirmed successfully"}), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/events', methods=['POST'])
def add_event():
    data = request.get_json()
    event = Event(name=data['name'], date=datetime.strptime(data['date'], '%Y-%m-%d'), location=data['location'], category=data['category'])
    db.session.add(event)
    db.session.commit()
    return jsonify({"message": "Event added successfully"}), 200

# Recommendation based on nearest neighbor (Room prices)
@app.route('/recommendations/rooms/<int:user_id>', methods=['GET'])
def recommend_rooms(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    rooms = Room.query.filter_by(available=True).all()
    if not rooms:
        return jsonify({"message": "No available rooms"}), 200

    room_data = np.array([[room.id, room.price] for room in rooms])
    user_bookings = Booking.query.filter_by(user_id=user_id).all()
    if not user_bookings:
        return jsonify({"message": "No previous bookings found"}), 200

    # Find rooms with similar prices
    booked_room_ids = [booking.room_id for booking in user_bookings]
    booked_rooms = Room.query.filter(Room.id.in_(booked_room_ids)).all()
    booked_prices = np.array([room.price for room in booked_rooms]).reshape(-1, 1)

    knn = NearestNeighbors(n_neighbors=3)
    knn.fit(room_data[:, 1].reshape(-1, 1))
    _, indices = knn.kneighbors(booked_prices)

    recommended_rooms = room_data[indices.flatten()][:, 0]
    recommendations = Room.query.filter(Room.id.in_(recommended_rooms)).all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in recommendations])

# Event recommendations based on user preferences
@app.route('/recommendations/events/<int:user_id>', methods=['GET'])
def recommend_events(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.preferences:
        return jsonify({"message": "No user preferences found"}), 200

    preferences = user.preferences.split(',')
    events = Event.query.all()
    recommended_events = [event for event in events if event.category in preferences]
    return jsonify([{ 'name': event.name, 'date': event.date.strftime('%Y-%m-%d'), 'location': event.location, 'category': event.category } for event in recommended_events])

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
