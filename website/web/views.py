from flask import Blueprint, render_template, request, jsonify, current_app


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