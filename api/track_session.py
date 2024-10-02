from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration for SQLAlchemy, Flask-Mail, and Flask-Login
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'

# Initialize Flask extensions
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
scheduler = BackgroundScheduler()

# Models for User and Interaction
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    total_time_spent = db.Column(db.Integer, default=0)  # in seconds

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref=db.backref('interactions', lazy=True))

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        login_user(user)
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"error": "User not found"}), 404

# User logout endpoint
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# Start user interaction (tracks time spent)
@app.route('/start_interaction', methods=['POST'])
@login_required
def start_interaction():
    interaction = Interaction(user_id=current_user.id, start_time=datetime.now())
    db.session.add(interaction)
    db.session.commit()
    return jsonify({"message": "Interaction started"}), 200

# End user interaction and calculate duration
@app.route('/end_interaction', methods=['POST'])
@login_required
def end_interaction():
    interaction = Interaction.query.filter_by(user_id=current_user.id, end_time=None).first()
    if interaction:
        interaction.end_time = datetime.now()
        duration = (interaction.end_time - interaction.start_time).total_seconds()
        current_user.total_time_spent += int(duration)
        db.session.commit()
        return jsonify({"message": "Interaction ended", "duration": duration}), 200
    return jsonify({"error": "No active interaction found"}), 404

# Send promotional emails based on user time spent on platform
def send_promotional_emails():
    users = User.query.all()
    for user in users:
        if user.total_time_spent > 3600:  # 1 hour
            discount = "30%"
        elif user.total_time_spent > 1800:  # 30 minutes
            discount = "20%"
        else:
            discount = "10%"
        msg = Message('Special Offer Just for You!', recipients=[user.email])
        msg.body = f'We appreciate your time on our platform. Enjoy a special {discount} discount on your next booking!'
        mail.send(msg)

# Schedule daily promotional email sending
scheduler.add_job(send_promotional_emails, 'interval', days=1)
scheduler.start()

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
