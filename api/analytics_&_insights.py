from flask import Flask, request, jsonify, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration for SQLAlchemy, Flask-Mail, and Scheduler
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'

# Initialize SQLAlchemy, Flask-Mail, and Scheduler
db = SQLAlchemy(app)
mail = Mail(app)
scheduler = BackgroundScheduler()

# Models for Room, Booking, Subscriber, and Event
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True))

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)

# Helper function to get room or return 404
def get_room_or_404(room_id):
    room = Room.query.get(room_id)
    if not room:
        abort(404, description=f"Room {room_id} not found")
    return room

# Home route displaying available rooms
@app.route('/')
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

# API to get all rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in rooms]), 200

# API to get details of a specific room
@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = get_room_or_404(room_id)
    return jsonify({
        'room_number': room.room_number,
        'room_type': room.room_type,
        'price': room.price,
        'available': room.available
    }), 200

# API to book a room
@app.route('/rooms/<int:room_id>/book', methods=['POST'])
def book_room(room_id):
    room = get_room_or_404(room_id)

    if not room.available:
        return jsonify({"error": f"Room {room.room_number} is already booked"}), 400

    data = request.get_json()
    try:
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        if check_in >= check_out:
            return jsonify({"error": "Check-out date must be after check-in date"}), 400
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid date format or missing check-in/check-out"}), 400

    booking = Booking(room_id=room.id, check_in=check_in, check_out=check_out, guest_name=data['guest_name'])
    room.available = False
    db.session.add(booking)
    db.session.commit()

    return jsonify({"message": f"Room {room.room_number} booked successfully"}), 200

# API to release a booked room
@app.route('/rooms/<int:room_id>/release', methods=['POST'])
def release_room(room_id):
    room = get_room_or_404(room_id)

    if room.available:
        return jsonify({"error": f"Room {room.room_number} is not currently booked"}), 400

    room.available = True
    db.session.commit()

    return jsonify({"message": f"Room {room.room_number} released successfully"}), 200

# API to subscribe to email promotions
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    if not Subscriber.query.filter_by(email=email).first():
        subscriber = Subscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()
        return jsonify({"message": "Subscribed successfully"}), 200
    return jsonify({"error": "Email is already subscribed"}), 400

# API to add an event
@app.route('/events', methods=['POST'])
def add_event():
    data = request.get_json()
    try:
        event_date = datetime.strptime(data['date'], '%Y-%m-%d')
        event = Event(name=data['name'], date=event_date, location=data['location'])
        db.session.add(event)
        db.session.commit()
        return jsonify({"message": "Event added successfully"}), 200
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid event data"}), 400

# Send promotional emails for upcoming events
def send_promotional_emails():
    today = datetime.today()
    upcoming_events = Event.query.filter(Event.date <= today + timedelta(days=7)).all()
    if upcoming_events:
        subscribers = Subscriber.query.all()
        for subscriber in subscribers:
            msg = Message('Upcoming Event Promotion!', recipients=[subscriber.email])
            msg.body = 'Don’t miss out on our special offers for upcoming events! Here are the details:'
            for event in upcoming_events:
                msg.body += f'\n- {event.name} on {event.date.strftime("%Y-%m-%d")} at {event.location}'
            mail.send(msg)
        print("Promotional emails sent successfully.")

# Scheduler to send promotional emails daily
scheduler.add_job(send_promotional_emails, 'interval', days=1)
scheduler.start()

# Initialize the database and start the Flask app
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
