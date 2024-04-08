from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from modules.database.database import db_blueprint, get_db

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('root'))
        else:
            flash('Incorrect Username or Password! Please check your details and try again.', 'warning')
    return render_template('login.html', title='Login')

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/newuser', methods=['POST'])
@login_required
def new_user():
    if request.method == 'POST':
        # Extract form data
        username = request.form['user_name']
        first_name = request.form['first_name']
        second_name = request.form['second_name']
        email_address = request.form['email_address']
        password = request.form['password']
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Create the user in the database
        conn = get_db()
        cursor = conn.cursor()
        try:
            # Check if the user already exists
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Username already exists. Please choose another one.', 'warning')
                return redirect(url_for('auth.login'))
                
            # Insert the new user into the database
            cursor.execute('INSERT INTO users (username, password_hash, first_name, second_name, email_address) VALUES (?, ?, ?, ?, ?)', 
                           (username, hashed_password, first_name, second_name, email_address))
            conn.commit()
            flash('User created successfully.', 'success')
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'danger')
        finally:
            conn.close()
            
        return redirect(url_for('auth.login'))

def add_default_user():
    username = 'admin'
    password = 'admin'  # You should choose a more secure password
    hashed_password = generate_password_hash(password)
    first_name = 'Aaron'
    second_name = 'Gomm'
    email_address = 'aaron.gomm@outlook.com'

    conn = get_db()
    cursor = conn.cursor()

    # Check if the user already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user is None:
        # Insert the default user since it does not exist
        cursor.execute('INSERT INTO users (username, password_hash, first_name, second_name, email_address) VALUES (?, ?, ?, ?, ?)', 
                       (username, hashed_password, first_name, second_name, email_address))
        conn.commit()
    conn.close()

class User(UserMixin):
    def __init__(self, id, username, password_hash, first_name, second_name):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.first_name = first_name
        self.second_name = second_name

    @staticmethod
    def get(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, first_name, second_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            # Make sure to pass all required arguments, including 'second_name'
            return User(user['id'], user['username'], user['password_hash'], user['first_name'], user['second_name'])
        return None


    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, first_name, second_name FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            return User(user['id'], user['username'], user['password_hash'], user['first_name'], user['second_name'])
        return None




