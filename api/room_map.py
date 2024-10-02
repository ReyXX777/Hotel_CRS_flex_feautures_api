from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Sample data representing the room map
rooms = {
    101: False,
    102: False,
    103: False,
    104: False,
    105: False,
    201: False,
    202: False,
    203: False,
    204: False,
    205: False
}

# Helper function to check room existence
def room_exists(room_id):
    if room_id not in rooms:
        abort(404, description=f"Room {room_id} not found")

@app.route('/rooms', methods=['GET'])
def get_rooms():
    """Retrieve the current status of all rooms."""
    return jsonify(rooms), 200

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Retrieve the status of a specific room."""
    room_exists(room_id)
    return jsonify({room_id: rooms[room_id]}), 200

@app.route('/rooms/<int:room_id>/reserve', methods=['POST'])
def reserve_room(room_id):
    """
    Reserve a specific room.
    Returns 400 if the room is already reserved.
    """
    room_exists(room_id)
    if rooms[room_id]:
        return jsonify({"error": f"Room {room_id} is already reserved"}), 400
    rooms[room_id] = True
    return jsonify({"message": f"Room {room_id} reserved successfully"}), 200

@app.route('/rooms/<int:room_id>/release', methods=['POST'])
def release_room(room_id):
    """
    Release a specific room.
    Returns 400 if the room is already unreserved.
    """
    room_exists(room_id)
    if not rooms[room_id]:
        return jsonify({"error": f"Room {room_id} is already unreserved"}), 400
    rooms[room_id] = False
    return jsonify({"message": f"Room {room_id} released successfully"}), 200

# Error handler for custom 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == '__main__':
    # Debug mode should be turned off in production
    app.run(debug=True)
