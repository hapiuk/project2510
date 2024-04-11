from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required
import sqlite3
from datetime import datetime
from modules.database.database import db_blueprint, get_db

equipment_blueprint = Blueprint('equipment_blueprint', __name__)

###################################################################################################################################### Equipment Functions


@equipment_blueprint.route('/equipment')
@login_required
def equipment():
    

    conn = get_db()
    equipment_details = conn.execute('SELECT e.*, u.first_name, u.second_name FROM equipment e JOIN users u ON e.owner = u.id').fetchall()
    users = conn.execute('SELECT id, first_name, second_name FROM users').fetchall()
    conn.close()

    generated_id = generate_asset_id()

    print(generated_id)

    return render_template('equipment.html', title='Equipment', equipment_details=equipment_details, users=users, generated_id=generated_id)

@equipment_blueprint.route('/addequipment', methods=['GET', 'POST'])
def add_equipment():
    if request.method == 'POST':
        asset_id = request.form['asset_id']
        asset_type = request.form['asset_type']
        status = request.form['status']
        owner = request.form['owner']
        purchase_date = request.form['purchase_date']
        asset_value = request.form['asset_value']
        current_value = request.form['current_value']
        warranty_start = request.form['warranty_start']
        warranty_end = request.form['warranty_end']
        warranty_provider = request.form['warranty_provider']
        asset_vendor = request.form['asset_vendor']
        serial_number = request.form['serial_number']
        imei = request.form['imei']
        mac = request.form['mac']

        conn = get_db()
        cursor = conn.cursor()

        # Insert equipment data into the database
        cursor.execute('''
            INSERT INTO equipment (asset_id, asset_type, status, owner, purchase_date, asset_value, current_value, warranty_start, warranty_end, warranty_provider, asset_vendor, serial_number, imei_1, mac_1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset_id, asset_type, status, owner, purchase_date, asset_value, current_value, warranty_start, warranty_end, warranty_provider, asset_vendor, serial_number, imei, mac))

        conn.commit()
        conn.close()

        return redirect(url_for('equipment_blueprint.equipment'))


@equipment_blueprint.route('/equipment/<asset_id>')
@login_required
def get_equipment_details(asset_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, u.first_name, u.second_name
        FROM equipment e
        JOIN users u ON e.owner = u.id
        WHERE e.asset_id = ?
    ''', (asset_id,))
    row = cursor.fetchone()

    if row:
        column_names = [description[0] for description in cursor.description]
        equipment_details = dict(zip(column_names, row))
        print("Equipment details:", equipment_details)  # Print the fetched equipment details
        
        # Fetch owner's first and last name from the users table
        owner_id = equipment_details['owner']
        owner_details = conn.execute('SELECT first_name, second_name FROM users WHERE id = ?', (owner_id,)).fetchone()
        owner_name = f"{owner_details['first_name']} {owner_details['second_name']}" if owner_details else None

        # Extract IMEI_1 and MAC_1 from the equipment details
        imei_1 = equipment_details.get('imei_1', '')
        mac_1 = equipment_details.get('mac_1', '')

        # Create a dictionary containing the equipment details
        equipment_dict = {
            'asset_id': equipment_details['asset_id'],
            'asset_type': equipment_details['asset_type'],
            'status': equipment_details['status'],
            'owner': owner_name,
            'purchase_date': equipment_details['purchase_date'],
            'asset_value': equipment_details['asset_value'],
            'current_value': equipment_details['current_value'],
            'warranty_start': equipment_details['warranty_start'],
            'warranty_end': equipment_details['warranty_end'],
            'warranty_provider': equipment_details['warranty_provider'],
            'asset_vendor': equipment_details['asset_vendor'],
            'serial_number': equipment_details['serial_number'],
            'imei_1': imei_1,
            'mac_1': mac_1
        }
        return jsonify(equipment_dict)
    else:
        # If the asset ID does not exist, return an error message
        return jsonify({'error': 'Equipment not found'})
    conn.close()


def generate_asset_id():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM equipment').fetchone()[0]  # Count items in equipment table
    conn.close()

    id_prefix = 'ISI'
    date_stamp = datetime.now().strftime('%Y%m%d')
    generated_id = f"{id_prefix}-{count + 1}-{date_stamp}"
    
    return generated_id

@equipment_blueprint.route('/delete_equipment', methods=['POST'])
def delete_equipment():
    if request.method == 'POST':
        # Get the asset ID from the request data
        asset_id = request.form['asset_id']

        # Perform the deletion operation (assuming you have a database table named 'equipment')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM equipment WHERE asset_id = ?', (asset_id,))
        conn.commit()
        conn.close()

        # Return a success message
        return jsonify({'message': 'Asset deleted successfully'})

    # If the request method is not POST, return an error message
    return jsonify({'error': 'Method not allowed'})

@equipment_blueprint.route('/update_equipment', methods=['POST'])
def update_equipment():
    if request.method == 'POST':
        # Extract the updated equipment details from the request
        asset_id = request.form.get('asset_id')
        asset_type = request.form.get('asset_type')
        status = request.form.get('status')
        owner = request.form.get('owner')
        purchase_date = request.form.get('purchase_date')
        asset_value = request.form.get('asset_value')
        current_value = request.form.get('current_value')
        warranty_start = request.form.get('warranty_start')
        warranty_end = request.form.get('warranty_end')
        warranty_provider = request.form.get('warranty_provider')
        asset_vendor = request.form.get('asset_vendor')
        serial_number = request.form.get('serial_number')
        imei_1 = request.form.get('imei')
        mac_1 = request.form.get('mac')

        # Update the equipment details in the database (assuming you have a table named 'equipment')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE equipment
            SET asset_type=?, status=?, owner=?, purchase_date=?, asset_value=?, current_value=?, warranty_start=?, warranty_end=?, warranty_provider=?, asset_vendor=?, serial_number=?, imei_1=?, mac_1=?
            WHERE asset_id=?
        """, (asset_type, status, owner, purchase_date, asset_value, current_value, warranty_start, warranty_end, warranty_provider, asset_vendor, serial_number, imei_1, mac_1, asset_id))
        conn.commit()
        conn.close()

        # Return a success message
        return jsonify({'message': 'Equipment details updated successfully'})

    # If the request method is not POST, return an error message
    return jsonify({'error': 'Method not allowed'})