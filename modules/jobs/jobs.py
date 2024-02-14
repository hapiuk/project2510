from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import sqlite3
from datetime import datetime
from modules.database.database import db_blueprint, get_db, get_all_clients, get_equipment_list, get_all_contracts

jobs_blueprint = Blueprint('jobs_blueprint', __name__)

@jobs_blueprint.route('/jobs')
def jobs():
    jobs = get_all_jobs() # Fetch all jobs from the database
    contracts = get_all_contracts()  # Fetch all contracts from the database
    clients = get_all_clients()  # Fetch all clients
    equipment = get_equipment_list()  # Fetch all equipment
    return render_template('jobs.html', title='Tasks', buttonName='Add Task', buttonTarget='add-task-modal')

def get_all_jobs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT jobs.*, clients.client_name
        FROM jobs
        JOIN clients ON jobs.client_account_number = clients.account_number
    ''')
    jobs = cursor.fetchall()
    conn.close()
    return [dict(job) for job in jobs]