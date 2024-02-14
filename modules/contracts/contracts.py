from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from datetime import datetime
from modules.database.database import db_blueprint, get_db, get_all_clients, get_all_contracts
from modules.equipment.equipment import get_equipment_list
import sqlite3
import calendar

contracts_blueprint = Blueprint('contracts_blueprint', __name__)


@contracts_blueprint.route('/contracts')
def contracts():
    contracts = get_all_contracts()  # Fetch all contracts from the database
    clients = get_all_clients()  # Fetch all clients
    equipment = get_equipment_list()  # Fetch all equipment
    return render_template('contracts.html', contracts=contracts, clients=clients, equipment=equipment, title='Contracts', buttonName='Add Contract', buttonTarget='new-contract-modal')

@contracts_blueprint.route('/create-contract', methods=['POST'])
def create_contract():
    if request.method == 'POST':
        client_account_number = request.form['client_account_number']
        equipment_ids = request.form.getlist('equipment[]')
        job_type = request.form['job_type']
        start_date_str = request.form['start_date']

        # Convert start_date string to datetime object
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        # Calculate the end date (12 months from the start date)
        end_date = add_months_to_date(start_date, 12)

        # Calculate renewal date (11 months from the start date)
        renewal_date = add_months_to_date(start_date, 11)

        contract_charge = request.form['contract_charge']
        billing_cycle = request.form['billing_cycle']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO contracts (
                          client_account_number, equipment_ids, job_type, start_date, end_date,
                          renewal_date, contract_charge, billing_cycle
                          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (client_account_number, ','.join(equipment_ids), job_type, start_date_str, 
                        end_date.strftime('%Y-%m-%d'), renewal_date.strftime('%Y-%m-%d'), contract_charge, billing_cycle))
        conn.commit()
        conn.close()

        return redirect(url_for('contracts_blueprint.contracts'))

@contracts_blueprint.route('/get-equipment-for-client/<account_number>')
def get_equipment_for_client(account_number):
    print("Received Account Number:", account_number)  # Debugging line
    equipment_rows = fetch_equipment_for_client(account_number)
    equipment = [dict(row) for row in equipment_rows]  # Convert rows to dictionaries
    print("Returning Equipment:", equipment)  # Debugging line
    return jsonify(equipment)  # Return equipment data as JSON

def get_contract_data(contract_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT contracts.*, clients.client_name
        FROM contracts
        INNER JOIN clients ON contracts.client_account_number = clients.account_number
        WHERE contracts.id = ?
    ''', (contract_id,))
    contract_data = cursor.fetchone()
    conn.close()
    return dict(contract_data) if contract_data else None

# Function to get equipment for a client based on account number
def fetch_equipment_for_client(account_number):
    print("Receiving Equipment Data")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM equipment WHERE client_account_number = ?
    ''', (account_number,))
    equipment = cursor.fetchall()
    conn.close()
    print("Received Equipment Data")
    return equipment

def get_contract_data(contract_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM contracts WHERE id = ?
    ''', (contract_id,))
    contract_data = cursor.fetchone()
    conn.close()
    return dict(contract_data) if contract_data else None

def get_equipment_for_ids(equipment_ids):
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM equipment WHERE id IN ({})'.format(','.join('?' for _ in equipment_ids))
    cursor.execute(query, equipment_ids)
    equipment_list = cursor.fetchall()
    conn.close()
    return [dict(eq) for eq in equipment_list]


def add_months_to_date(original_date, months):
    # Add the specified number of months to the original date
    month = original_date.month - 1 + months
    year = original_date.year + month // 12
    month = month % 12 + 1
    day = min(original_date.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)