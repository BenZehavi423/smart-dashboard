from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from .models import User
from .db_manager import MongoDBManager
from .validation import Validator
import bcrypt
from functools import wraps


#create a blueprint for auth routes
auth = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
    
#route for user registration
@auth.route('/register', methods=['GET', 'POST'])
def register():

    if 'username' in session:
        return redirect(url_for('views.profile'))
    
    if request.method == 'POST':
        #read form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Sanitize inputs
        username = Validator.sanitize_input(username)
        password = Validator.sanitize_input(password)
        
        # Validate input
        username_valid, username_error = Validator.validate_username(username)
        password_valid, password_error = Validator.validate_password(password)
        
        if not username_valid:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': username_error}), 400
            flash(username_error, 'error')
            return redirect(url_for('auth.register'))
        
        if not password_valid:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': password_error}), 400
            flash(password_error, 'error')
            return redirect(url_for('auth.register'))
        
        #check if user already exists
        existing_user = current_app.db.get_user_by_username(username)
        if existing_user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Username already exists!'}), 400
            flash('Username already exists!', 'error')
            return redirect(url_for('auth.register'))
        
        #hash the password
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        #create a new user object
        user = User(username=username, password_hash=hashed_pw)

        #save the user to the database
        current_app.db.create_user(user)

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('views.profile'))
    
    #if GET request, render the registration template
    return render_template('register.html')
    

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('views.profile'))
     
    if request.method == 'POST':
        # Read form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Sanitize inputs
        username = Validator.sanitize_input(username)
        password = Validator.sanitize_input(password)
        # Check if user exists and password is correct
        user = current_app.db.get_user_by_username(username)
        if user and user.password_hash and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            # Store user information in session
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('views.profile'))
        else:
            # Provide more specific error messages
            if not user:
                error_message = 'Username not found. Please check your username or create a new account.'
            else:
                error_message = 'Incorrect password. Please try again.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': error_message}), 400
            else:
                flash(error_message, 'error')
                return redirect(url_for('auth.login'))
    return render_template('login.html'), 200

@auth.route('/login_with_logout')
def login_with_logout():
    # If user is logged in, log them out when visiting login page
    if 'username' in session:
        session.pop('username', None)
        flash('You have been logged out.', 'success')
    
    return redirect(url_for('auth.login'))

@auth.route('/register_with_logout')
def register_with_logout():
    # If user is logged in, log them out when visiting register page
    if 'username' in session:
        session.pop('username', None)
        flash('You have been logged out.', 'success')
    
    return redirect(url_for('auth.register'))


@auth.route('/logout')
def logout():
     session.pop('username', None)
     flash('You have been logged out.', 'success')
     return redirect(url_for('views.home'))



