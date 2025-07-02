from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, flash
import os
from .auth import login_required
from .csv_processor import process_file

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
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    user = current_app.db.get_user_by_username(session['username'])
    if request.method == 'POST':
        files = request.files.getlist('file')
        failed_files = []
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                proccesed_file = process_file(file)
                current_app.db.create_file(proccesed_file)
            else:
                failed_files.append(f"Invalid file: {getattr(file, 'filename', 'unknown')}")
        if len(failed_files) != 0:
            flash(f'Failed to upload {len(failed_files)} files.', 'error')
        else:
            flash('All files uploaded successfully!', 'success')
        return jsonify({
            'success': len(failed_files) == 0,
            'failed_files': failed_files,
        })
    # GET: render page with user's files
    user_files = current_app.db.get_files_for_user(user)
    return render_template('upload_files.html', files=user_files)