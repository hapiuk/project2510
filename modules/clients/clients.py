from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session
import sqlite3
from datetime import datetime
from modules.database.database import db_blueprint, get_db, get_all_clients

clients_blueprint = Blueprint('clients_blueprint', __name__)

@clients_blueprint.route('/clients')
def clients():
    search_query = request.args.get('search', '', type=str)
    success_message = request.args.get('success', '')
    error_message = request.args.get('error', '')

    conn = get_db()

    if search_query:
        # Implement filtering based on the search query
        query = '''
            SELECT * FROM clients
            WHERE account_number LIKE ? OR client_name LIKE ? OR address_line_1 LIKE ?
            OR address_line_2 LIKE ? OR town_city LIKE ? OR county LIKE ?
            OR postcode LIKE ? OR phone_number LIKE ? OR status LIKE ?
            ORDER BY id
        '''
        search_params = (f"%{search_query}%",) * 8
        clients = conn.execute(query, search_params).fetchall()
    else:
        clients = conn.execute('''
            SELECT * FROM clients
            ORDER BY id
        ''').fetchall()

    conn.close()
    return render_template('clients.html', clients=clients, success_message=success_message, error_message=error_message)

@clients_blueprint.route('/create-client', methods=['POST'])
def create_client():
    if request.method == 'POST':
        try:
            # Get data from the form
            account_number = request.form['account_number']
            client_name = request.form['client_name']
            address_line_1 = request.form['address_line_1']
            address_line_2 = request.form['address_line_2']
            town_city = request.form['town_city']
            county = request.form['county']
            postcode = request.form['postcode']
            phone_number = request.form['phone_number']
            status = request.form['status']
            date_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Save the client data to the database
            conn = get_db()
            conn.execute('''
                INSERT INTO clients (account_number, client_name, address_line_1, address_line_2, town_city, county, postcode, phone_number, status, date_stamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (account_number, client_name, address_line_1, address_line_2, town_city, county, postcode, phone_number, status, date_stamp))
            conn.commit()
            conn.close()

            success_message = "Client added successfully."
            session['success_message'] = success_message
        except Exception as e:
            error_message = str(e)
            session['error_message'] = error_message

    return redirect('/clients')

@clients_blueprint.route('/update-client', methods=['POST'])
def update_client():
    if request.method == 'POST':
        try:
            # Get data from the form
            account_number = request.form['account_number']
            client_name = request.form['client_name']
            address_line_1 = request.form['address_line_1']
            address_line_2 = request.form['address_line_2']
            town_city = request.form['town_city']
            county = request.form['county']
            postcode = request.form['postcode']
            phone_number = request.form['phone_number']
            email = request.form['email']
            status = request.form['status']

            # Update the client data in the database
            conn = get_db()
            conn.execute('''
                UPDATE clients
                SET client_name=?, address_line_1=?, address_line_2=?, town_city=?, county=?, postcode=?, status=?
                WHERE account_number=?
            ''', (client_name, address_line_1, address_line_2, town_city, county, postcode,  status, account_number))
            conn.commit()
            conn.close()

            success_message = "Client updated successfully."
            session['success_message'] = success_message
        except Exception as e:
            error_message = str(e)
            session['error_message'] = error_message
            print(f"Error updating client: {error_message}")

    return redirect('/clients')

@clients_blueprint.route('/download-client-template', methods=['GET'])
def download_client_template():
    template_file = 'templates/clients_template.csv'  # Path to your CSV template

    # Set the content type to indicate it's a CSV file
    return send_file(template_file, as_attachment=True, mimetype='text/csv')
