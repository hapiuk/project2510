import os
import random
import string
import subprocess
import logging
import csv
from io import TextIOWrapper
from flask import Flask, request, flash, render_template, redirect, jsonify, session, send_from_directory, url_for, send_file
from flask_login import login_user, logout_user, login_required, current_user, LoginManager, UserMixin
from werkzeug.utils import secure_filename
import io
import zipfile
import sqlite3
import shutil
from datetime import datetime, timedelta
from modules.database.database import db_blueprint, get_db, get_all_clients
from modules.clients.clients import clients_blueprint
from modules.equipment.equipment import equipment_blueprint
from modules.contracts.contracts import contracts_blueprint
from modules.jobs.jobs import jobs_blueprint
from modules.auth.auth import auth_blueprint, add_default_user, User


app = Flask(__name__)
app.debug = True
app.secret_key = 'topsecret'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

add_default_user()

# Register Blueprints
app.register_blueprint(db_blueprint)
app.register_blueprint(clients_blueprint)
app.register_blueprint(equipment_blueprint)
app.register_blueprint(contracts_blueprint)
app.register_blueprint(jobs_blueprint)
app.register_blueprint(auth_blueprint)


@app.route('/', methods=['GET'])
@login_required
def root():
    return render_template('index.html', title='Dashboard')


if __name__ == "__main__":
    import socket

    def is_valid_ip(ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    ip_address = None
    while True:
        ip_address = input("Enter the IP address to run the app (e.g., 0.0.0.0): ")
        if is_valid_ip(ip_address):
            break
        else:
            print("Invalid IP address. Please enter a valid IP address.")

    print(f"Running the app at IP address: {ip_address}")

    app.secret_key = 'topsecret'
    app.run(host=ip_address, port=5000, debug=True)
