from flask import Flask, request, jsonify, abort

app = Flask(__name__)

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

# List to store promotions
promotions = []

# Helper function to check occupancy rate
def check_occupancy():
    total_rooms = len(rooms)
    occupied_rooms = sum(rooms.values())
    occupancy_rate = occupied_rooms / total_rooms
    return occupancy_rate

# Helper function to launch a promotion
def launch_promotion():
    promotion_id = len(promotions) + 1
    promotion = {
        "id": promotion_id,
        "description": "Special discount for low occupancy!",
        "discount": "20%"
    }
    promotions.append(promotion)
    return promotion

# Helper function to check if a room exists
def room_exists(room_id):
    if room_id not in rooms:
        abort(404, description=f"Room {room_id} not found")

# Helper function to check if a promotion already exists
def promotion_already_exists():
    return any(promo for promo in promotions if promo["description"] == "Special discount for low occupancy!")

# Route to get the status of all rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    return jsonify(rooms), 200

# Route to reserve a room
@app.route('/rooms/<int:room_id>/reserve', methods=['POST'])
def reserve_room(room_id):
    room_exists(room_id)
    
    if rooms[room_id]:
        return jsonify({"error": f"Room {room_id} is already reserved"}), 400

    rooms[room_id] = True
    return jsonify({"message": f"Room {room_id} reserved successfully"}), 200

# Route to release a room
@app.route('/rooms/<int:room_id>/release', methods=['POST'])
def release_room(room_id):
    room_exists(room_id)
    
    if not rooms[room_id]:
        return jsonify({"error": f"Room {room_id} is already unreserved"}), 400

    rooms[room_id] = False
    return jsonify({"message": f"Room {room_id} released successfully"}), 200

# Route to check current occupancy rate
@app.route('/occupancy', methods=['GET'])
def get_occupancy():
    occupancy_rate = check_occupancy()
    return jsonify({"occupancy_rate": occupancy_rate}), 200

# Route to get all available promotions
@app.route('/promotions', methods=['GET'])
def get_promotions():
    return jsonify(promotions), 200

# Route to launch a promotion if the occupancy is below a threshold
@app.route('/promotions/launch', methods=['POST'])
def launch_promotion_endpoint():
    occupancy_rate = check_occupancy()
    
    if occupancy_rate >= 0.5:
        return jsonify({"message": "Occupancy rate is sufficient, no promotion needed"}), 200
    
    if promotion_already_exists():
        return jsonify({"message": "A promotion is already running due to low occupancy"}), 400
    
    promotion = launch_promotion()
    return jsonify(promotion), 200

# Error handler for custom 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == '__main__':
    app.run(debug=True)
