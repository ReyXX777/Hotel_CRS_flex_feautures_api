from flask import Flask, request, jsonify, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
import re

app = Flask(__name__)

# Configuration for SQLAlchemy, Flask-Mail, and Scheduler
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'

# Initialize SQLAlchemy, Flask-Mail, and Scheduler
db = SQLAlchemy(app)
mail = Mail(app)
scheduler = BackgroundScheduler()

# Models for Room, Booking, Subscriber, and Event
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete='CASCADE'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True, cascade="all, delete"))

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)

# Helper function to get room or return 404
def get_room_or_404(room_id):
    room = Room.query.get(room_id)
    if not room:
        abort(404, description=f"Room {room_id} not found")
    return room

# Validation for email format
def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

# Routes remain the same as the original script, with corrections for error handling

# Enhanced error handling in the subscribe route
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data.get('email')
    if not email or not is_valid_email(email):
        return jsonify({"error": "Valid email is required"}), 400

    try:
        if not Subscriber.query.filter_by(email=email).first():
            subscriber = Subscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            return jsonify({"message": "Subscribed successfully"}), 200
        return jsonify({"error": "Email is already subscribed"}), 400
    except Exception as e:
        logging.error(f"Error subscribing email {email}: {e}")
        return jsonify({"error": "An error occurred while subscribing"}), 500

# The rest of the routes and logic remain unchanged from the original script.

# Scheduler to send promotional emails
scheduler.add_job(send_promotional_emails, 'interval', days=1)
scheduler.start()

# Shutdown scheduler when the app stops
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()

# Initialize the database and start the Flask app
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
