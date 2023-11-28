from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import sqlite3
from datetime import datetime
from modules.database.database import db_blueprint, get_db, get_all_clients, get_all_contracts
from modules.equipment.equipment import get_equipment_list

contracts_blueprint = Blueprint('contracts_blueprint', __name__)


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

@contracts_blueprint.route('/get-equipment-for-client/<account_number>')
def get_equipment_for_client(account_number):
    print("Received Account Number:", account_number)  # Debugging line
    equipment_rows = fetch_equipment_for_client(account_number)
    equipment = [dict(row) for row in equipment_rows]  # Convert rows to dictionaries
    print("Returning Equipment:", equipment)  # Debugging line
    return jsonify(equipment)  # Return equipment data as JSON

@contracts_blueprint.route('/contracts')
def contracts():
    contracts = get_all_contracts()  # Fetch all contracts from the database
    clients = get_all_clients()  # Fetch all clients
    equipment = get_equipment_list()  # Fetch all equipment
    return render_template('contracts.html', contracts=contracts, clients=clients, equipment=equipment)

@contracts_blueprint.route('/contract-details/<contract_id>')
def contract_details(contract_id):
    # Fetch contract data based on contract_id
    contract_data = get_contract_data(contract_id)
    if contract_data:
        # Fetch equipment list for the contract
        equipment_ids = contract_data['equipment_ids'].split(',')
        equipment_list = get_equipment_for_ids(equipment_ids)
        contract_data['equipment_list'] = equipment_list

        return render_template('contract_details.html', contract=contract_data)
    else:
        # Handle the case where no contract is found
        flash('Contract not found', 'error')
        return redirect(url_for('contracts'))

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
        date_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO contracts (
                          client_account_number, equipment_ids, job_type, start_date, end_date,
                          renewal_date, contract_charge, billing_cycle, date_stamp
                          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (client_account_number, ','.join(equipment_ids), job_type, start_date_str, 
                        end_date.strftime('%Y-%m-%d'), renewal_date.strftime('%Y-%m-%d'), contract_charge, billing_cycle, date_stamp))
        conn.commit()
        conn.close()

        return redirect(url_for('contracts'))

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