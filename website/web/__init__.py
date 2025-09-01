from flask import Flask
from .views import views
import os
from .db_manager import MongoDBManager
from .auth import auth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

socketio = SocketIO()
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key_for_development")
    # Initialize the rate limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )

    # This line sets a default MongoDB URI only when the app is run locally outside of Docker.
    # It has no effect inside Docker, since the database URI is hardcoded in MongoDBManager as "mongodb://db:27017".
    os.environ.setdefault(
        "MONGO_URI",
        "mongodb://localhost:27017/smart_dashboard"
    )
    
    app.db = MongoDBManager()

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Initialize Socket.IO with the app
    socketio.init_app(app)

    from . import sockets

    return app