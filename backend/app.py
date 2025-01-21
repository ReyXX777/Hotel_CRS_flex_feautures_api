from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

# Initialize Flask app and extensions
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'user.login'
CORS(app)  # Enable CORS for cross-origin requests

# Import routes
from routes import user_routes, room_routes

# Register blueprints
app.register_blueprint(user_routes, url_prefix="/users")
app.register_blueprint(room_routes, url_prefix="/rooms")

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return {"error": "Resource not found"}, 404

if __name__ == "__main__":
    app.run(debug=True)
