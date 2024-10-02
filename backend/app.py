from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialize Flask app and extensions
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'user.login'

# Import routes
from routes import user_routes, room_routes

# Register blueprints
app.register_blueprint(user_routes, url_prefix="/users")
app.register_blueprint(room_routes, url_prefix="/rooms")

if __name__ == "__main__":
    app.run(debug=True)
