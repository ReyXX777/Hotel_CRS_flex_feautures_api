from flask import Flask, request, jsonify, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
db = SQLAlchemy(app)

# Room model to store room details
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)

# Booking model to store guest booking information
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True))

# Helper function to validate room existence
def get_room_or_404(room_id):
    room = Room.query.get(room_id)
    if not room:
        abort(404, description=f"Room {room_id} not found")
    return room

# Helper function to validate dates
def parse_dates(data):
    try:
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        if check_in >= check_out:
            abort(400, description="Check-out date must be after check-in date")
        return check_in, check_out
    except (KeyError, ValueError):
        abort(400, description="Invalid date format or missing check-in/check-out")

# Home route with a dynamic index.html page showing room details
@app.route('/')
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

# API to get details of all rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{
        'room_number': room.room_number,
        'room_type': room.room_type,
        'price': room.price,
        'available': room.available
    } for room in rooms]), 200

# API to get details of all available rooms
@app.route('/rooms/available', methods=['GET'])
def get_available_rooms():
    available_rooms = Room.query.filter_by(available=True).all()
    return jsonify([{
        'room_number': room.room_number,
        'room_type': room.room_type,
        'price': room.price,
        'available': room.available
    } for room in available_rooms]), 200

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
        return jsonify({"error": f"Room {room.room_number} is already booked"}), 400

    data = request.get_json()
    check_in, check_out = parse_dates(data)

    booking = Booking(
        room_id=room.id, 
        check_in=check_in, 
        check_out=check_out, 
        guest_name=data['guest_name']
    )
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

# API to get all bookings
@app.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([{
        'id': booking.id,
        'room_id': booking.room_id,
        'check_in': booking.check_in.strftime('%Y-%m-%d'),
        'check_out': booking.check_out.strftime('%Y-%m-%d'),
        'guest_name': booking.guest_name
    } for booking in bookings]), 200

# API to get bookings for a specific room
@app.route('/rooms/<int:room_id>/bookings', methods=['GET'])
def get_bookings_for_room(room_id):
    room = get_room_or_404(room_id)
    bookings = Booking.query.filter_by(room_id=room_id).all()
    return jsonify([{
        'id': booking.id,
        'check_in': booking.check_in.strftime('%Y-%m-%d'),
        'check_out': booking.check_out.strftime('%Y-%m-%d'),
        'guest_name': booking.guest_name
    } for booking in bookings]), 200

# API to cancel a booking
@app.route('/bookings/<int:booking_id>/cancel', methods=['DELETE'])
def cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    room = Room.query.get(booking.room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    room.available = True
    db.session.delete(booking)
    db.session.commit()

    return jsonify({"message": f"Booking {booking_id} canceled successfully"}), 200

# Custom error handler for 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Custom error handler for 400 errors
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

# Initialize the database and start the app
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
