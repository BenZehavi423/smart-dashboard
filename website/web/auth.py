from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .models import User
from .db_manager import MongoDBManager
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
    if request.method == 'POST':
        #read form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        #check if any fileds are empty
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('auth.register'))
        
        #check if user already exists
        existing_user = current_app.db.get_user_by_username(username)
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('auth.register'))
        
        #hash the password
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        #create a new user object
        user = User(username=username, email=email, password_hash=hashed_pw)

        #save the user to the database
        current_app.db.create_user(user)

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    #if GET request, render the registration template
    return render_template('register.html')
    

@auth.route('/login', methods=['GET', 'POST'])
def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#         if not username or not password:
#             flash('Both username and password are required.', 'error')
#             return redirect(url_for('auth.login'))
#         user = current_app.db.get_user_by_username(username)
#         if user and user.password_hash and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
#             session['username'] = user.username
#             flash('Logged in successfully!', 'success')
#             return redirect(url_for('views.profile'))
#         else:
#             flash('Invalid username or password.', 'error')
#             return redirect(url_for('auth.login'))
    return render_template('login.html'), 200

# @auth.route('/logout')
# def logout():
#     session.pop('username', None)
#     flash('You have been logged out.', 'success')
#     return redirect(url_for('auth.login'))



