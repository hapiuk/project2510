from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required
import sqlite3
from datetime import datetime
from modules.database.database import get_db

engineer_assets_blueprint = Blueprint('engineer_assets_blueprint', __name__)




@engineer_assets_blueprint.route('/engineer_assets')
@login_required
def engineer_assets():
    conn = get_db()
    # Set row_factory to return dictionaries
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT e.*, u.first_name, u.second_name 
        FROM eng_equipment e 
        JOIN users u ON e.owner = u.id
    ''')
    engineer_assets = cursor.fetchall()

    users = conn.execute('SELECT id, first_name, second_name FROM users').fetchall()
    conn.close()

    generated_id = generate_asset_id()

    print("Engineer Assets:", engineer_assets)  # Debug statement

    return render_template('engineer_assets.html', title='Engineer Assets', engineer_assets=engineer_assets, users=users, generated_id=generated_id)

@engineer_assets_blueprint.route('/add_engineer_equipment', methods=['POST'])
def add_engineer_asset():
    if request.method == 'POST':
        asset_id = request.form['asset_id']
        owner = request.form['owner']
        serial_number = request.form['serial_number']
        asset_type = request.form['asset_type']
        status = request.form['status']
        calibration_date = request.form['calibration_date']
        calibration_expiry = request.form['calibration_expiry']
        calibration_status = request.form['calibration_status']
        calibration_cert = request.form['calibration_cert']
        calibration_company = request.form['calibration_company']
        calibration_standard = request.form['calibration_standard']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO eng_equipment (asset_id, owner, serial_number, asset_type, status, calibration_date, calibration_expiry, calibration_status, calibration_cert, calibration_company, calibration_standard)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset_id, owner, serial_number, asset_type, status, calibration_date, calibration_expiry, calibration_status, calibration_cert, calibration_company, calibration_standard))

        conn.commit()
        conn.close()

        return redirect(url_for('engineer_assets_blueprint.engineer_assets'))

@engineer_assets_blueprint.route('/get_engineer_asset_details/<id>')
@login_required
def get_engineer_asset_details(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, u.first_name, u.second_name
        FROM eng_equipment e
        JOIN users u ON e.owner = u.id
        WHERE e.id = ?
    ''', (id,))
    row = cursor.fetchone()

    if row:
        column_names = [description[0] for description in cursor.description]
        asset_details = dict(zip(column_names, row))
        print("Engineer asset details:", asset_details)  # Print the fetched engineer asset details
        
        # Fetch owner's first and last name from the users table
        owner_id = asset_details['owner']
        owner_details = conn.execute('SELECT first_name, second_name FROM users WHERE id = ?', (owner_id,)).fetchone()
        owner_name = f"{owner_details['first_name']} {owner_details['second_name']}" if owner_details else None

        # Create a dictionary containing the engineer asset details
        engineer_asset_dict = {
            'id': asset_details['id'],
            'asset_id': asset_details['asset_id'],
            'owner': owner_name,
            'serial_number': asset_details['serial_number'],
            'asset_type': asset_details['asset_type'],
            'status': asset_details['status'],
            'calibration_date': asset_details['calibration_date'],
            'calibration_expiry': asset_details['calibration_expiry'],
            'calibration_status': asset_details['calibration_status'],
            'calibration_cert': asset_details['calibration_cert'],
            'calibration_company': asset_details['calibration_company'],
            'calibration_standard': asset_details['calibration_standard']
        }
        return jsonify(engineer_asset_dict)
    else:
        # If the id does not exist, return an error message
        return jsonify({'error': 'Engineer Asset not found'})
    conn.close()


def generate_asset_id():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM eng_equipment').fetchone()[0]  # Count items in eng_equipment table
    conn.close()

    id_prefix = 'ENG'
    date_stamp = datetime.now().strftime('%Y%m%d')
    generated_id = f"{id_prefix}-{count + 1}-{date_stamp}"
    
    return generated_id

@engineer_assets_blueprint.route('/delete_engineer_asset', methods=['POST'])
def delete_engineer_asset():
    if request.method == 'POST':
        asset_id = request.form['asset_id']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM eng_equipment WHERE asset_id = ?', (asset_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Asset deleted successfully'})

    return jsonify({'error': 'Method not allowed'})


@engineer_assets_blueprint.route('/update_engineer_asset', methods=['POST'])
def update_engineer_asset():
    if request.method == 'POST':
        asset_id = request.form['asset_id']
        owner = request.form['owner']
        serial_number = request.form['serial_number']
        asset_type = request.form['asset_type']
        status = request.form['status']
        calibration_date = request.form['calibration_date']
        calibration_expiry = request.form['calibration_expiry']
        calibration_status = request.form['calibration_status']
        calibration_cert = request.form['calibration_cert']
        calibration_company = request.form['calibration_company']
        calibration_standard = request.form['calibration_standard']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE eng_equipment
            SET owner=?, serial_number=?, asset_type=?, status=?, calibration_date=?, calibration_expiry=?, calibration_status=?, calibration_cert=?, calibration_company=?, calibration_standard=?
            WHERE asset_id=?
        ''', (owner, serial_number, asset_type, status, calibration_date, calibration_expiry, calibration_status, calibration_cert, calibration_company, calibration_standard, asset_id))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Asset updated successfully'})

    return jsonify({'error': 'Method not allowed'})



