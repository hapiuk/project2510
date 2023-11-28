from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import sqlite3
from datetime import datetime
from modules.database.database import db_blueprint, get_db, get_all_clients

equipment_blueprint = Blueprint('equipment_blueprint', __name__)


###################################################################################################################################### Equipment Functions

@equipment_blueprint.route('/download-template', methods=['GET'])
def download_template():
    template_file = 'templates/equipment_template.csv'  # Path to your CSV template

    # Set the content type to indicate it's a CSV file
    return send_file(template_file, as_attachment=True, mimetype='text/csv')

@equipment_blueprint.route('/upload-equipment', methods=['POST'])
def upload_equipment():
    if 'csv_file' in request.files:
        try:
            # Process the uploaded CSV file
            equipment_data = process_equipment_csv(request.files['csv_file'])
            
            # Insert equipment data into the database
            insert_equipment_from_csv(equipment_data)
            
            flash('CSV file uploaded and equipment details added successfully', 'success')
        except Exception as e:
            flash(f'Error processing CSV file: {str(e)}', 'error')

    return redirect('/equipment')

def insert_equipment_from_csv(equipment_data):
    conn = get_db()
    cursor = conn.cursor()
    
    for equipment in equipment_data:
        cursor.execute('''
            INSERT INTO equipment (equipment_number, client_account_number, equipment_type, equipment_sub_type, serial_number)
            VALUES (?, ?, ?, ?, ?)
        ''', (equipment['equipment_number'], equipment['client_account_number'], equipment['equipment_type'], equipment['equipment_sub_type'], equipment['serial_number']))
    
    conn.commit()
    conn.close()

def process_equipment_csv(file):
    equipment_data = []

    csv_file = TextIOWrapper(file, encoding='utf-8')
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        print("CSV Row:", row)
        # Check if 'client_account_number' is in the CSV row (without the BOM character)
        if 'client_account_number' not in row:
            raise ValueError("Missing 'client_account_number' in CSV row")

        # Extract Info (use 'client_account_number' as the column name)
        client_account_number = row.get('client_account_number', 'Unknown')
        equipment_number = row.get('equipment_number', 'Unknown')
        equipment_type = row.get('equipment_type', 'Unknown')
        equipment_sub_type = row.get('equipment_sub_type', 'Unknown')
        serial_number = row.get('serial_number', 'Unknown')
        client_asset_id = row.get('client_asset_id', 'Unknown')
        sub_location = row.get('sub_location', 'Unknown')
        safe_working_load = row.get('safe_working_load', 'Unknown')
        inspection_frequency = row.get('inspection_frequency', 'Unknown')
        year_of_manufacture = row.get('year_of_manufacture', 'Unknown')

        equipment_data.append({
            'equipment_number': equipment_number,
            'client_account_number': client_account_number,
            'equipment_type': equipment_type,
            'equipment_sub_type': equipment_sub_type,
            'serial_number': serial_number,
            'client_asset_id': client_asset_id,
            'sub_location': sub_location,
            'safe_working_load': safe_working_load,
            'inspection_frequency': inspection_frequency,
            'year_of_manufacture': year_of_manufacture,
        })


    return equipment_data

# Function to fetch equipment data
def get_equipment_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT equipment.*, clients.client_name
        FROM equipment
        INNER JOIN clients ON equipment.client_account_number = clients.account_number
    ''')
    equipment = cursor.fetchall()
    conn.close()
    return equipment

# Function to fetch equipment details based on equipment_id
def get_equipment_details(equipment_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM equipment WHERE id = ?', (equipment_id,))
    equipment_details = cursor.fetchone()
    conn.close()
    return dict(equipment_details) if equipment_details else None

def get_client_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, client_name FROM clients')
    clients = cursor.fetchall()
    conn.close()
    return clients

# Function to insert equipment data
def insert_equipment(equipment_number, client_account_number, equipment_type, equipment_sub_type, serial_number, client_asset_id, sub_location, safe_working_load, inspection_frequency, year_of_manufacture):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO equipment (equipment_number, client_account_number, equipment_type, equipment_sub_type, '
                   'serial_number, client_asset_id, sub_location, safe_working_load, inspection_frequency, year_of_manufacture) '
                   'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (equipment_number, client_account_number, equipment_type, equipment_sub_type, serial_number, client_asset_id, sub_location,
                    safe_working_load, inspection_frequency, year_of_manufacture))
    conn.commit()
    cursor.close()


@equipment_blueprint.route('/update-equipment', methods=['POST'])
def update_equipment():
    if request.method == 'POST':
        equipment_number = request.form.get('equipment_number')
        client_account_number = request.form.get('client_account_number')
        equipment_type = request.form.get('equipment_type')
        equipment_sub_type = request.form.get('equipment_sub_type')
        serial_number = request.form.get('serial_number')
        client_asset_id = request.form.get('client_asset_id')
        sub_location = request.form.get('sub_location')
        safe_working_load = request.form.get('safe_working_load')
        inspection_frequency = request.form.get('inspection_frequency')
        year_of_manufacture = request.form.get('year_of_manufacture')

        try:
            conn = get_db()
            sql_query = '''
                UPDATE equipment
                SET equipment_type=?, equipment_sub_type=?, serial_number=?, client_asset_id=?, 
                sub_location=?, safe_working_load=?, inspection_frequency=?, year_of_manufacture=?
                WHERE equipment_number=?
            '''
            conn.execute(sql_query, (equipment_type, equipment_sub_type, serial_number, client_asset_id, sub_location,
                safe_working_load, inspection_frequency, year_of_manufacture, equipment_number))
            conn.commit()
            conn.close()

            success_message = "Equipment updated successfully."
            session['success_message'] = success_message
        except Exception as e:
            error_message = str(e)
            session['error_message'] = error_message

    return redirect('/equipment')

@equipment_blueprint.route('/equipment')
def equipment():
    equipment = get_equipment_list()
    clients = get_all_clients()
    search_query = request.args.get('search', '', type=str)

    # Apply filtering based on search query
    if search_query:
        equipment = [item for item in equipment if search_query.lower() in str(item).lower()]

    return render_template(
        'equipment.html',
        equipment=equipment,
        clients=clients,
        search_query=search_query
    )


@equipment_blueprint.route('/equipment/create', methods=['POST'])
def create_equipment():
    if request.method == 'POST':

        # Process the uploaded CSV file and obtain equipment data
        equipment_data = process_equipment_csv(request.files['csv_file'])

        # Insert equipment data into the database, including client_account_number from CSV
        for equipment in equipment_data:
            equipment_number = equipment['equipment_number']
            client_account_number = equipment['client_account_number']
            equipment_type = equipment['equipment_type']
            equipment_sub_type = equipment['equipment_sub_type']
            serial_number = equipment['serial_number']
            client_asset_id = equipment['client_asset_id']
            sub_location = equipment['sub_location']
            safe_working_load = equipment['safe_working_load']
            inspection_frequency = equipment['inspection_frequency']
            year_of_manufacture = equipment['year_of_manufacture']
            date_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            insert_equipment(equipment_number, client_account_number, equipment_type, equipment_sub_type, serial_number,
                             client_asset_id, sub_location, safe_working_load, inspection_frequency, year_of_manufacture, date_stamp)


        response_data = {"message": "Equipment added successfully."}
        return jsonify(response_data)
        return redirect('/equipment')


@equipment_blueprint.route('/equipment/search', methods=['GET'])
def equipment_search():
    search_query = request.args.get('search', '')
    equipment = get_equipment_list()

    if search_query:
        equipment = [item for item in equipment if search_query.lower() in str(item).lower()]

    return jsonify(equipment)