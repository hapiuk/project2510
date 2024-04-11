from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
from modules.database.database import db_blueprint, get_db

# Create a blueprint for engineer assets
engineer_assets_blueprint = Blueprint('engineer_assets_blueprint', __name__)

# Define routes for engineer assets CRUD operations
@engineer_assets_blueprint.route('/engineer_assets')
@login_required
def engineer_assets():
    conn = get_db()
    engineer_assets = conn.execute('SELECT * FROM eng_equipment').fetchall()
    conn.close()
    return render_template('engineer_assets.html', title='Engineer Assets', engineer_assets=engineer_assets)

@engineer_assets_blueprint.route('/add_engineer_asset', methods=['POST'])
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

@engineer_assets_blueprint.route('/update_engineer_asset', methods=['POST'])
def update_engineer_asset():
    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        owner = request.form.get('owner')
        serial_number = request.form.get('serial_number')
        asset_type = request.form.get('asset_type')
        status = request.form.get('status')
        calibration_date = request.form.get('calibration_date')
        calibration_expiry = request.form.get('calibration_expiry')
        calibration_status = request.form.get('calibration_status')
        calibration_cert = request.form.get('calibration_cert')
        calibration_company = request.form.get('calibration_company')
        calibration_standard = request.form.get('calibration_standard')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE eng_equipment
            SET owner=?, serial_number=?, asset_type=?, status=?, calibration_date=?, calibration_expiry=?, calibration_status=?, calibration_cert=?, calibration_company=?, calibration_standard=?
            WHERE asset_id=?
        """, (owner, serial_number, asset_type, status, calibration_date, calibration_expiry, calibration_status, calibration_cert, calibration_company, calibration_standard, asset_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Engineer asset details updated successfully'})

@engineer_assets_blueprint.route('/delete_engineer_asset', methods=['POST'])
def delete_engineer_asset():
    if request.method == 'POST':
        asset_id = request.form['asset_id']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM eng_equipment WHERE asset_id = ?', (asset_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Engineer asset deleted successfully'})

@engineer_assets_blueprint.route('/engineer_assets/<asset_id>')
@login_required
def get_engineer_asset_details(asset_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM eng_equipment WHERE asset_id = ?', (asset_id,))
    row = cursor.fetchone()

    if row:
        column_names = [description[0] for description in cursor.description]
        engineer_asset_details = dict(zip(column_names, row))
        return jsonify(engineer_asset_details)
    else:
        return jsonify({'error': 'Engineer asset not found'})

@engineer_assets_blueprint.route('/generate_asset_id')
def generate_asset_id():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM eng_equipment').fetchone()[0]
    conn.close()

    id_prefix = 'ENG'
    date_stamp = datetime.now().strftime('%Y%m%d')
    generated_id = f"{id_prefix}-{count + 1}-{date_stamp}"
    
    return jsonify({'asset_id': generated_id})
