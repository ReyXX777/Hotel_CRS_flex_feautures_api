from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Sample data representing rooms and reservations
rooms = {
    1: {"type": "Single", "price": 100, "available": True},
    2: {"type": "Double", "price": 150, "available": True},
    3: {"type": "Suite", "price": 300, "available": True}
}

reservations = []

def validate_reservation_data(data):
    """Helper function to validate reservation data."""
    required_fields = ['room_id', 'guest_name', 'check_in', 'check_out']
    for field in required_fields:
        if field not in data:
            return False, f"'{field}' is required"
    
    # Validate dates
    try:
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        if check_in >= check_out:
            return False, "Check-out date must be after check-in date"
    except ValueError:
        return False, "Invalid date format. Use 'YYYY-MM-DD'"
    
    return True, ""

@app.route('/rooms', methods=['GET'])
def get_rooms():
    """Get all rooms and their availability."""
    return jsonify(rooms), 200

@app.route('/rooms/available', methods=['GET'])
def get_available_rooms():
    """Get all available rooms."""
    available_rooms = {room_id: room for room_id, room in rooms.items() if room['available']}
    return jsonify(available_rooms), 200

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Get details of a specific room by room_id."""
    room = rooms.get(room_id)
    if room:
        return jsonify(room), 200
    return jsonify({"error": "Room not found"}), 404

@app.route('/reservations', methods=['GET'])
def get_reservations():
    """Get all reservations."""
    return jsonify(reservations), 200

@app.route('/reservations/room/<int:room_id>', methods=['GET'])
def get_reservations_for_room(room_id):
    """Get all reservations for a specific room."""
    room_reservations = [r for r in reservations if r['room_id'] == room_id]
    return jsonify(room_reservations), 200

@app.route('/reservations', methods=['POST'])
def create_reservation():
    """Create a new reservation for a room."""
    data = request.json
    
    # Validate reservation data
    is_valid, message = validate_reservation_data(data)
    if not is_valid:
        return jsonify({"error": message}), 400

    room_id = data.get('room_id')

    # Check if the room exists and is available
    if room_id not in rooms or not rooms[room_id]['available']:
        return jsonify({"error": "Room not available"}), 400
    
    reservation = {
        "id": len(reservations) + 1,
        "room_id": room_id,
        "guest_name": data.get('guest_name'),
        "check_in": data.get('check_in'),
        "check_out": data.get('check_out')
    }
    reservations.append(reservation)
    rooms[room_id]['available'] = False

    return jsonify({"message": "Reservation created successfully", "reservation": reservation}), 201

@app.route('/reservations/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    """Get a specific reservation by reservation_id."""
    reservation = next((r for r in reservations if r['id'] == reservation_id), None)
    if reservation:
        return jsonify(reservation), 200
    return jsonify({"error": "Reservation not found"}), 404

@app.route('/reservations/<int:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id):
    """Delete a reservation by reservation_id."""
    global reservations
    reservation = next((r for r in reservations if r['id'] == reservation_id), None)
    
    if reservation:
        reservations = [r for r in reservations if r['id'] != reservation_id]
        rooms[reservation['room_id']]['available'] = True
        return jsonify({"message": "Reservation cancelled successfully"}), 200
    
    return jsonify({"error": "Reservation not found"}), 404

@app.route('/reservations/<int:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id):
    """Update an existing reservation."""
    data = request.json
    reservation = next((r for r in reservations if r['id'] == reservation_id), None)
    
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404
    
    # Validate reservation data (optional fields can be updated)
    is_valid, message = validate_reservation_data(data)
    if not is_valid:
        return jsonify({"error": message}), 400

    room_id = data.get('room_id')
    # If changing room, check if the new room is available
    if room_id != reservation['room_id']:
        if room_id not in rooms or not rooms[room_id]['available']:
            return jsonify({"error": "New room not available"}), 400
        # Free the old room and assign the new one
        rooms[reservation['room_id']]['available'] = True
        rooms[room_id]['available'] = False

    reservation.update({
        "room_id": room_id,
        "guest_name": data.get('guest_name'),
        "check_in": data.get('check_in'),
        "check_out": data.get('check_out')
    })

    return jsonify({"message": "Reservation updated successfully", "reservation": reservation}), 200

if __name__ == '__main__':
    app.run(debug=True)
