from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Sample data representing the room map with room type, price, and availability
rooms = {
    101: {"type": "Single", "price": 100, "available": True},
    102: {"type": "Double", "price": 150, "available": True},
    103: {"type": "Suite", "price": 300, "available": True},
    104: {"type": "Single", "price": 100, "available": True},
    105: {"type": "Double", "price": 150, "available": True},
    201: {"type": "Single", "price": 100, "available": True},
    202: {"type": "Double", "price": 150, "available": True},
    203: {"type": "Suite", "price": 300, "available": True},
    204: {"type": "Single", "price": 100, "available": True},
    205: {"type": "Double", "price": 150, "available": True}
}

# Helper function to check if room exists
def room_exists(room_id):
    room = rooms.get(room_id)
    if not room:
        abort(404, description=f"Room {room_id} not found")
    return room

# Route to get a list of all available rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    available_rooms = {room_id: details for room_id, details in rooms.items() if details['available']}
    return jsonify(available_rooms), 200

# Route to get details of a specific room
@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = room_exists(room_id)
    return jsonify(room), 200

# Route to reserve a room
@app.route('/rooms/<int:room_id>/reserve', methods=['POST'])
def reserve_room(room_id):
    room = room_exists(room_id)
    
    if room['available']:
        room['available'] = False
        return jsonify({"message": f"Room {room_id} reserved successfully", "room": room}), 200
    return jsonify({"error": f"Room {room_id} is not available"}), 400

# Route to release a reserved room
@app.route('/rooms/<int:room_id>/release', methods=['POST'])
def release_room(room_id):
    room = room_exists(room_id)
    
    if not room['available']:
        room['available'] = True
        return jsonify({"message": f"Room {room_id} released successfully", "room": room}), 200
    return jsonify({"error": f"Room {room_id} is not reserved"}), 400

# Error handler for custom 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == '__main__':
    app.run(debug=True)
