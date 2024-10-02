from flask import request, jsonify
from models import Room, Booking
from app import db
from services.recommendation_service import recommend_rooms

@room_routes.route('/', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{ 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price, 'available': room.available } for room in rooms])

@room_routes.route('/<int:room_id>/book', methods=['POST'])
def book_room(room_id):
    room = Room.query.get(room_id)
    if room and room.available:
        data = request.get_json()
        booking = Booking(user_id=data['user_id'], room_id=room_id)
        room.available = False
        db.session.add(booking)
        db.session.commit()
        return jsonify({"message": "Room booked successfully"}), 200
    return jsonify({"error": "Room not available"}), 400
