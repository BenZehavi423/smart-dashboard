from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, flash
import os
from .auth import login_required
from .csv_processor import process_file
import requests

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@views.route('/upload_files', methods=['GET', 'POST'])
@login_required
def upload_files():
    # Check if user is logged in
    # If not, redirect to login page
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    user = current_app.db.get_user_by_username(session['username'])

    # Handle file upload via AJAX post request
    # POST: process uploaded files
    if request.method == 'POST':
        files = request.files.getlist('file')
        failed_files = []

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                try:
                    #Process the file and attach user_id + preview
                    processed_file = process_file(file, user._id)
                    current_app.db.create_file(processed_file)

                except Exception as e:
                    # If processing fails, log the error
                    failed_files.append(f"{file.filename}: {str(e)}")

            # If file is not valid, log the error
            else:
                failed_files.append(f"Invalid file: {getattr(file, 'filename', 'unknown')}")

        # Return JSON response to the frontend
        return jsonify({
            'success': len(failed_files) == 0,
            'failed_files': failed_files,
            'files': [f.filename for f in current_app.db.get_files_for_user(user)]
        })

    #GET: render the upload page with current user's files
    user_files = current_app.db.get_files_for_user(user)
    return render_template('upload_files.html', files=user_files)

@views.route('/ask_llm', methods=['POST'])
@login_required
def ask_llm():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # The service name 'llm_service' is used as the hostname
        llm_api_url = 'http://llm_service:5001/predict'
        response = requests.post(llm_api_url, json={'query': query})
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        # Log the error e
        return jsonify({'error': 'The LLM service is currently unavailable.'}), 503