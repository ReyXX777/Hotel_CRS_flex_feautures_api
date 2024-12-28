from flask import Blueprint, request, jsonify
from datetime import datetime
from ..backend.models import Room, Booking, db

# Create a Blueprint for available_slot routes
available_slot_bp = Blueprint('available_slot', __name__)

# Helper function to check room availability
def is_room_available(room_id, check_in, check_out):
    """
    Check if a room is available for the given dates.
    """
    conflicting_bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.check_in < check_out,
        Booking.check_out > check_in
    ).all()
    return len(conflicting_bookings) == 0

# API to get available rooms for a date range
@available_slot_bp.route('/available', methods=['GET'])
def get_available_rooms():
    """
    Get all available rooms for a given date range.
    Query Parameters:
        check_in (str): Check-in date in 'YYYY-MM-DD' format.
        check_out (str): Check-out date in 'YYYY-MM-DD' format.
    """
    # Get query parameters
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')

    # Validate query parameters
    if not check_in_str or not check_out_str:
        return jsonify({"error": "Both check_in and check_out dates are required"}), 400

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d')
        if check_in >= check_out:
            return jsonify({"error": "Check-out date must be after check-in date"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'"}), 400

    # Get all rooms
    rooms = Room.query.all()
    available_rooms = []

    # Check availability for each room
    for room in rooms:
        if is_room_available(room.id, check_in, check_out):
            available_rooms.append({
                'room_id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'price': room.price
            })

    return jsonify(available_rooms), 200

# API to check availability of a specific room
@available_slot_bp.route('/available/<int:room_id>', methods=['GET'])
def check_room_availability(room_id):
    """
    Check if a specific room is available for a given date range.
    Query Parameters:
        check_in (str): Check-in date in 'YYYY-MM-DD' format.
        check_out (str): Check-out date in 'YYYY-MM-DD' format.
    """
    # Get query parameters
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')

    # Validate query parameters
    if not check_in_str or not check_out_str:
        return jsonify({"error": "Both check_in and check_out dates are required"}), 400

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d')
        if check_in >= check_out:
            return jsonify({"error": "Check-out date must be after check-in date"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'"}), 400

    # Check if the room exists
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": f"Room {room_id} not found"}), 404

    # Check availability
    if is_room_available(room_id, check_in, check_out):
        return jsonify({
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': room.price,
            'available': True
        }), 200
    else:
        return jsonify({
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'price': room.price,
            'available': False
        }), 200
