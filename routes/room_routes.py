from flask import Blueprint, request, jsonify, abort
from models import Room, Booking
from app import db
from services.recommendation_service import recommend_rooms

# Blueprint for room-related routes
room_routes = Blueprint('room_routes', __name__)

# Get all rooms
@room_routes.route('/', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    if not rooms:
        return jsonify({"error": "No rooms found"}), 404

    rooms_data = [
        {
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': room.price,
            'available': room.available,
        }
        for room in rooms
    ]
    return jsonify(rooms_data), 200

# Book a room
@room_routes.route('/<int:room_id>/book', methods=['POST'])
def book_room(room_id):
    room = Room.query.get(room_id)

    if not room:
        return jsonify({"error": f"Room with ID {room_id} not found"}), 404

    if not room.available:
        return jsonify({"error": f"Room {room.room_number} is already booked"}), 400

    try:
        # Extract and validate input data
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "User ID is required to book a room"}), 400

        # Create a booking
        booking = Booking(user_id=user_id, room_id=room_id)
        room.available = False

        # Persist the changes
        db.session.add(booking)
        db.session.commit()

        return jsonify({"message": f"Room {room.room_number} booked successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
