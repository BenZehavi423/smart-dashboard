from flask import Blueprint, render_template, request, jsonify, current_app, session
from .auth import login_required

# Blueprint lets us organize routes into different files
# we don't have to put all routes in the "views.py" module
views = Blueprint('views', __name__)


# Define the routes for the views blueprint
@views.route('/')
def home():
    # Return a simple HTML response for the home page
    # 200 is the "OK" HTTP status code

    #files = list(current_app.db.db.files.find({})) add later
    return render_template('home.html'), 200

@views.route('/profile')
@login_required
def profile():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    return render_template('profile.html', user=user), 200

@views.route('/upload_files')
@login_required
def upload_files():
    return render_template('upload_files.html'), 200