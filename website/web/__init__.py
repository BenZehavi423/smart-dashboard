from flask import Flask
from .views import views
import os
from .db_manager import MongoDBManager
def create_app():
    app = Flask(__name__)

    os.environ.setdefault(
        "MONGO_URI",
        "mongodb://localhost:27017/smart_dashboard"
    )
    app.db = MongoDBManager()

    app.register_blueprint(views, url_prefix='/')

    return app