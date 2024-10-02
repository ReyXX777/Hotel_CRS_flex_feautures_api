from flask import Flask, render_template, jsonify, request, abort
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Sample data representing the room map (False = unreserved, True = reserved)
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

# Helper function to validate if a room exists
def room_exists(room_id):
    if room_id not in rooms:
        abort(404, description=f"Room {room_id} not found")

# Helper function to send room update via SocketIO
def send_room_update(room_id, status):
    socketio.emit('update_room', {'room_id': room_id, 'status': status}, broadcast=True)

@app.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """API endpoint to get the status of all rooms."""
    return jsonify(rooms), 200

@app.route('/api/rooms/<int:room_id>/reserve', methods=['POST'])
def reserve_room(room_id):
    """Reserve a room if it's available."""
    room_exists(room_id)
    if rooms[room_id]:
        return jsonify({"error": f"Room {room_id} is already reserved"}), 400

    rooms[room_id] = True
    send_room_update(room_id, True)  # Emit room status to all connected clients
    return jsonify({"message": f"Room {room_id} reserved successfully"}), 200

@app.route('/api/rooms/<int:room_id>/release', methods=['POST'])
def release_room(room_id):
    """Release a room if it's currently reserved."""
    room_exists(room_id)
    if not rooms[room_id]:
        return jsonify({"error": f"Room {room_id} is already unreserved"}), 400

    rooms[room_id] = False
    send_room_update(room_id, False)  # Emit room status to all connected clients
    return jsonify({"message": f"Room {room_id} released successfully"}), 200

# Error handler for custom 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == '__main__':
    # Concurrency handling is built-in with Flask-SocketIO
    # Ensure that you have eventlet or gevent installed in production
    socketio.run(app, debug=True)
