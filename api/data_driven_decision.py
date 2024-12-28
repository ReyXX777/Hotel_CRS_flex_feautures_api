from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
db = SQLAlchemy(app)

# Room model representing rooms in the hotel
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)

# Reservation model representing reservations made by guests
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    room = db.relationship('Room', backref=db.backref('reservations', lazy=True))

# Helper function to validate room existence
def get_room_or_404(room_id):
    room = Room.query.get(room_id)
    if not room:
        abort(404, description=f"Room {room_id} not found")
    return room

# Helper function to parse dates
def parse_dates(data):
    try:
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        if check_in >= check_out:
            abort(400, description="Check-out date must be after check-in date")
        return check_in, check_out
    except (KeyError, ValueError):
        abort(400, description="Invalid date format or missing check-in/check-out")

# Route to get all rooms with their details
@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in rooms]), 200

# Route to get details of a specific room by room_id
@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = get_room_or_404(room_id)
    return jsonify({ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available }), 200

# Route to reserve a room
@app.route('/rooms/<int:room_id>/reserve', methods=['POST'])
def reserve_room(room_id):
    room = get_room_or_404(room_id)

    if not room.available:
        return jsonify({"error": "Room is already reserved"}), 400

    data = request.get_json()
    check_in, check_out = parse_dates(data)

    # Create reservation
    reservation = Reservation(room_id=room.id, check_in=check_in, check_out=check_out, guest_name=data['guest_name'])
    room.available = False  # Mark room as unavailable
    db.session.add(reservation)
    db.session.commit()

    return jsonify({"message": f"Room {room.room_number} reserved successfully", "reservation_id": reservation.id}), 200

# Route to release a reserved room
@app.route('/rooms/<int:room_id>/release', methods=['POST'])
def release_room(room_id):
    room = get_room_or_404(room_id)

    if room.available:
        return jsonify({"error": "Room is not reserved"}), 400

    # Mark room as available again
    room.available = True
    db.session.commit()

    return jsonify({"message": f"Room {room.room_number} released successfully"}), 200

# Route to get all reservations
@app.route('/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify([{ 'id': reservation.id, 'room_id': reservation.room_id, 'check_in': reservation.check_in.strftime('%Y-%m-%d'), 'check_out': reservation.check_out.strftime('%Y-%m-%d'), 'guest_name': reservation.guest_name } for reservation in reservations]), 200

# Route to get reservations for a specific room
@app.route('/rooms/<int:room_id>/reservations', methods=['GET'])
def get_room_reservations(room_id):
    room = get_room_or_404(room_id)
    reservations = Reservation.query.filter_by(room_id=room_id).all()
    return jsonify([{ 'id': reservation.id, 'check_in': reservation.check_in.strftime('%Y-%m-%d'), 'check_out': reservation.check_out.strftime('%Y-%m-%d'), 'guest_name': reservation.guest_name } for reservation in reservations]), 200

# Route to cancel a reservation
@app.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404

    room = Room.query.get(reservation.room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    room.available = True  # Mark room as available again
    db.session.delete(reservation)
    db.session.commit()

    return jsonify({"message": f"Reservation {reservation_id} canceled successfully"}), 200

# Route to get insights like total reservations, peak times, and guest preferences
@app.route('/insights', methods=['GET'])
def get_insights():
    total_reservations = Reservation.query.count()

    peak_times = db.session.query(
        db.func.strftime('%Y-%m', Reservation.check_in), 
        db.func.count(Reservation.id)
    ).group_by(db.func.strftime('%Y-%m', Reservation.check_in)).all()

    guest_preferences = db.session.query(
        Room.room_type, 
        db.func.count(Reservation.id)
    ).join(Reservation).group_by(Room.room_type).all()

    insights = {
        "total_reservations": total_reservations,
        "peak_times": [{"month": month, "reservations": count} for month, count in peak_times],
        "guest_preferences": [{"room_type": room_type, "reservations": count} for room_type, count in guest_preferences]
    }

    return jsonify(insights), 200

# Custom error handler for 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Custom error handler for 400
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

# Initialize the database and start the Flask app
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
