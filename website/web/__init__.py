from flask import Flask
from .views import views
import os
from .db_manager import MongoDBManager
from .auth import auth

def create_app():
    app = Flask(__name__)
    app.secret_key = "very-secret-key"  # 🔒 REPLACE in production
    
    # This line sets a default MongoDB URI only when the app is run locally outside of Docker.
    # It has no effect inside Docker, since the database URI is hardcoded in MongoDBManager as "mongodb://db:27017".
    os.environ.setdefault(
        "MONGO_URI",
        "mongodb://localhost:27017/smart_dashboard"
    )
    
    app.db = MongoDBManager()

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app