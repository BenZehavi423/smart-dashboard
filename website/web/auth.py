from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .models import User
from .db_manager import MongoDBManager
import bcrypt

#create a blueprint for auth routes
auth = Blueprint('auth', __name__)

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
    

@auth.route('/login', methods=['GET'])
def login():
    return render_template('login.html')



