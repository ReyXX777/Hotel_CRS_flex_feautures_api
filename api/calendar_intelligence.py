from flask import Flask, request, jsonify, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta

app = Flask(__name__)

# Configurations for SQLAlchemy and Flask-Mail
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'

# Initialize SQLAlchemy and Flask-Mail
db = SQLAlchemy(app)
mail = Mail(app)

# Room model representing hotel rooms
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)

# Booking model representing room bookings
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True))

# Subscriber model representing email subscribers
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Helper function to check if a room exists
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

# API to get details of all rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in rooms]), 200

# API to get details of a specific room by room_id
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
        return jsonify({"error": "Room is already booked"}), 400

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
        return jsonify({"error": "Room is not currently booked"}), 400

    room.available = True
    db.session.commit()

    return jsonify({"message": f"Room {room.room_number} released successfully"}), 200

# API to subscribe to the hotel's mailing list
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

# Check if it's the festive season (e.g., Christmas or New Year)
def is_festive_season():
    today = datetime.today()
    festive_dates = [
        datetime(today.year, 12, 25),  # Christmas
        datetime(today.year, 1, 1),    # New Year
    ]
    return any(today <= date <= today + timedelta(days=7) for date in festive_dates)

# Send promotional emails to all subscribers
def send_promotional_emails():
    if is_festive_season():
        subscribers = Subscriber.query.all()
        for subscriber in subscribers:
            msg = Message('Festive Season Offer!', recipients=[subscriber.email])
            msg.body = 'Enjoy our special festive season discounts at our hotel! Book now and save!'
            mail.send(msg)
        print("Promotional emails sent successfully.")

# Initialize the database and start the app
if __name__ == '__main__':
    db.create_all()
    send_promotional_emails()
    app.run(debug=True)
