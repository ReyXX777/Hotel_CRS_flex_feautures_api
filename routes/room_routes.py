from flask import Blueprint, request, jsonify, abort
from models import Room, Booking
from app import db
from services.recommendation_service import recommend_rooms
from datetime import datetime  # Added for booking timestamps
from utils.validation import validate_booking_data  # Added for input validation

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
            'description': room.description,  # Added room description
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
        validation_error = validate_booking_data(data)  # Added input validation
        if validation_error:
            return jsonify({"error": validation_error}), 400

        user_id = data.get('user_id')

        # Create a booking with timestamp
        booking = Booking(
            user_id=user_id,
            room_id=room_id,
            booked_at=datetime.utcnow()  # Added booking timestamp
        )
        room.available = False

        # Persist the changes
        db.session.add(booking)
        db.session.commit()

        return jsonify({"message": f"Room {room.room_number} booked successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Get room recommendations
@room_routes.route('/recommendations', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        user_preferences = data.get('preferences')

        if not user_preferences:
            return jsonify({"error": "Preferences are required for recommendations"}), 400

        recommendations = recommend_rooms(user_preferences)
        return jsonify(recommendations), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
