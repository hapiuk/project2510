from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime

db_blueprint = Blueprint('db_blueprint', __name__)

DATABASE = './static/trackex.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_user_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            second_name TEXT,
            type TEXT,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_forms_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forms (
            id INTEGER PRIMARY KEY,
            form_number TEXT NOT NULL,
            job_number TEXT NOT NULL,
            equipment_number TEXT NOT NULL,
            job_date DATE,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_jobtypes_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobtypes (
            id INTEGER PRIMARY KEY,
            job_type TEXT NOT NULL,
            type_description TEXT,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_jobs_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            client_account_number TEXT NOT NULL,
            client_name TEXT,
            client_address TEXT,
            job_type TEXT,
            due_date DATE,
            equipment_ids TEXT,
            job_status TEXT,
            notes TEXT,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_contracts_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY,
            client_account_number TEXT NOT NULL,
            equipment_ids TEXT,
            job_type TEXT,
            start_date DATE,
            end_date DATE,
            renewal_date DATE,
            contract_charge NUMERIC,
            billing_cycle TEXT,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_clients_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT,
            client_name TEXT,
            address_line_1 TEXT,
            address_line_2 TEXT,
            town_city TEXT,
            county TEXT,
            postcode TEXT,
            phone_number TEXT,
            email TEXT,
            status TEXT,
            notes TEXT,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_equipment_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_number TEXT,
            client_account_number TEXT,
            equipment_type TEXT,
            equipment_sub_type TEXT,
            serial_number TEXT,
            client_asset_id TEXT,
            sub_location TEXT,
            safe_working_load REAL,
            inspection_frequency TEXT,
            price NUMERIC,
            timing NUMERIC,
            year_of_manufacture INTEGER,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_all_clients():
    conn = get_db()
    cursor = conn.cursor()
    query = '''SELECT * FROM clients'''  # Adjust the SQL query as needed
    cursor.execute(query)
    clients = cursor.fetchall()
    conn.close()
    return clients

def get_all_contracts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT contracts.*, clients.client_name
        FROM contracts
        JOIN clients ON contracts.client_account_number = clients.account_number
    ''')
    contracts = cursor.fetchall()
    conn.close()
    return [dict(contract) for contract in contracts]

def get_client_details(account_number):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE account_number = ?', (account_number,))
    client_details = cursor.fetchone()
    conn.close()
    return dict(client_details) if client_details else None

def get_equipment_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM equipment')
    equipment_list = cursor.fetchall()
    conn.close()
    return equipment_list

def generate_equipment_number():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(equipment_number) FROM equipment')
    last_equipment_number = cursor.fetchone()[0]

    if last_equipment_number is not None:
        numeric_part = int(last_equipment_number[3:])
        new_numeric_part = numeric_part + 1
        new_equipment_number = f'EQP{str(new_numeric_part).zfill(3)}'
    else:
        new_equipment_number = 'EQP000'

    conn.close()
    return new_equipment_number

def get_all_clients():
    conn = get_db()
    cursor = conn.cursor()
    query = '''SELECT * FROM clients'''  # Adjust the SQL query as needed
    cursor.execute(query)
    clients = cursor.fetchall()
    conn.close()
    return clients

create_equipment_table()
create_clients_table()
create_contracts_table()
create_jobs_table()
create_jobtypes_table()
create_forms_table()
create_user_table()