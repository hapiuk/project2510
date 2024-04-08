from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from modules.database.database import db_blueprint, get_db, get_all_clients, get_client_details
from PyPDF2 import PdfMerger

import logging

import zipfile
import shutil
import os
import re
import pdfplumber
import csv
import datetime


aecom_blueprint = Blueprint('aecom_blueprint', __name__)

UPLOAD_FOLDER = './input'
OUTPUT_FOLDER = './output'
PROCESSED_FOLDER = './processed'
TEMP_DOWNLOAD_FOLDER = './output'
ALLOWED_EXTENSIONS = {'pdf'}


def count_severity_levels(get_db):
    # Connect to the database
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Count occurrences of each severity level
        cursor.execute("SELECT COUNT(*) FROM aecom_inspection WHERE priority = 'Moderate'")
        moderate_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM aecom_inspection WHERE priority = 'Substantial'")
        substantial_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM aecom_inspection WHERE priority = 'Intolerable'")
        intolerable_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM aecom_inspection")
        defect_count = cursor.fetchone()[0]

        return moderate_count, substantial_count, intolerable_count, defect_count
    finally:
        conn.close()

@aecom_blueprint.route('/aecom', methods=['GET', 'POST'])
@login_required
def aecom():

    if request.method == 'POST':
        # Clear the input folder
        clear_input_folder(UPLOAD_FOLDER)
        # Get Form Details
        business_entity = request.form['business_entity']
        invoice_value = request.form['invoice_value']
        invoice_group = request.form['invoice_group']
        # Process file uploads
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                print(f"{filename} uploaded successfully.")
            else:
                print("Invalid file type.")

        # Process the uploaded files
        business_entity = request.form.get('business_entity', '')
        invoice_value = request.form.get('invoice_value', '')
        invoice_group = request.form.get('invoice_group', '')
        try:
            main_merged_pdf_path, faulty_reports_path, csv_file, csv_additional_file, first_report_date, date_str, additional_info_for_db = process_puwer_documents(UPLOAD_FOLDER, OUTPUT_FOLDER, PROCESSED_FOLDER, business_entity, get_db, invoice_group, invoice_value)
            # Prepare files for download
            files_to_zip = []
            for root, _, files in os.walk(OUTPUT_FOLDER):
                for file in files:
                    if file.startswith(f"{business_entity}-PWR-") or file.startswith(f"{business_entity}-FAULTYREPORTS-"):
                        files_to_zip.append(os.path.join(root, file))

            if not files_to_zip:
                print("No files found for the specified business entity.")
                return redirect(url_for('aecom_blueprint.aecom'))

            temp_folder = os.path.join(TEMP_DOWNLOAD_FOLDER, business_entity)
            os.makedirs(temp_folder, exist_ok=True)

            for file_to_zip in files_to_zip:
                shutil.move(file_to_zip, os.path.join(temp_folder, os.path.basename(file_to_zip)))

            zip_filename = f"{business_entity}_output.zip"
            zip_path = os.path.join(TEMP_DOWNLOAD_FOLDER, zip_filename)
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for file in os.listdir(temp_folder):
                    zip_file.write(os.path.join(temp_folder, file), file)

            shutil.rmtree(temp_folder)
            print("Files processed and zipped successfully.")

            # Redirect to the 'aecom' page to refresh
            return redirect(url_for('aecom_blueprint.aecom'))

        except Exception as e:
            error_message = f"Error processing files: {str(e)}, business_entity: {business_entity}, invoice_group: {invoice_group}, invoice_value: {invoice_value}"
            print(error_message)
            raise

    # Fetch data from aecom_reports table
    conn = get_db()

    aecom_reports = conn.execute('SELECT * FROM aecom_reports ORDER BY id').fetchall()
    aecom_sites = conn.execute('SELECT * FROM aecom_sites ORDER BY id').fetchall()
    aecom_defects = conn.execute('SELECT * FROM aecom_inspection ORDER BY id').fetchall()

    # Calculate total reports 
    unique_site_count = conn.execute('SELECT COUNT(DISTINCT inspection_ref) FROM aecom_reports').fetchone()[0]

    # Calculate total invoice value
    total_invoice_value = conn.execute('SELECT SUM(invoice_value) FROM aecom_reports').fetchone()[0]

    # Calculate average reponse time
    average_processing_time = calculate_average_processing_time(get_db)

    entity_to_site = {}
    entity_site_mapping = conn.execute('SELECT business_entity, location_name FROM aecom_sites')

    for entity, site in entity_site_mapping:
        entity_to_site[entity] = site

    # Count occurrences of each severity level
    moderate_count, substantial_count, intolerable_count, defect_count = count_severity_levels(get_db)

    print(f"Moderate Count: {moderate_count}")

    conn.close()

    return render_template('aecom.html', aecom_reports=aecom_reports, aecom_sites=aecom_sites, aecom_defects=aecom_defects, unique_site_count=unique_site_count, entity_to_site=entity_to_site, total_invoice_value=total_invoice_value, moderate_count=moderate_count, substantial_count=substantial_count, intolerable_count=intolerable_count, defect_count=defect_count, average_process_time=average_processing_time)


def clear_input_folder(upload_folder):
    pdf_files = [file for file in os.listdir(upload_folder) if file.endswith('.pdf')]
    for pdf_file in pdf_files:
        file_path = os.path.join(upload_folder, pdf_file)
        os.remove(file_path)
        print(f"Deleted: {file_path}")

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_information(text, business_entity):

    inspection_no = re.search(r"#InspectionID#\s*(\d+)", text)
    job_no = re.search(r"#JobID#\s*(\d+)", text)
    client_id = re.search(r"#ClientID#\s*(.+)", text)
    serial_no = re.search(r"#SerialNumber#\s*(.+)", text)
    date = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)

    intolerable = re.search(r"Intolerable - Defects requiring immediate action\s*(.+)", text)
    substantial = re.search(r"Substantial - Defects requiring attention within a(?:\stime period)?\s*(.+)", text)
    moderate = re.search(r"Moderate - Other defects requiring attention\s*(.+)", text)

    priority = ""
    if intolerable and intolerable.group(1).strip().lower() not in ["", "none"]:
        priority = "Intolerable"
    elif substantial and substantial.group(1).strip().lower() not in ["", "none"]:
        priority = "Substantial"
    elif moderate and moderate.group(1).strip().lower() not in ["", "none"]:
        priority = "Moderate"

    remedial_works = []
    if intolerable and intolerable.group(1).strip().lower() != "none":
        remedial_works.append(intolerable.group(1).strip())
    if substantial and substantial.group(1).strip().lower() != "none":
        remedial_works.append(substantial.group(1).strip())
    if moderate and moderate.group(1).strip().lower() != "none":
        remedial_works.append(moderate.group(1).strip())

    remedial_works_notes = " ".join(remedial_works)

    if date:
        date_action_raised = datetime.datetime.strptime(date.group(1), "%d/%m/%Y")
        formatted_date = date_action_raised.strftime("%d%m%Y")

        if priority == "Moderate":
            target_date = date_action_raised + datetime.timedelta(days=180)
        elif priority == "Substantial":
            target_date = date_action_raised + datetime.timedelta(days=30)
        elif priority == "Intolerable":
            target_date = date_action_raised + datetime.timedelta(days=7)
        else:
            target_date = None

        if target_date:
            target_completion_date = target_date.strftime("%d/%m/%Y")
        else:
            target_completion_date = ""
    else:
        target_completion_date = ""

    # Determine if remedial works were processed
    remedial_works_processed = bool(remedial_works)

    # Update the value for "Remedial Works" dynamically
    remedial_works_value = "Yes" if remedial_works_processed else "No"

    first_report_date = None

    if first_report_date is None:
                    date_match = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)
                    if date_match:
                        first_report_date = datetime.datetime.strptime(date_match.group(1), "%d/%m/%Y")

    date_str = first_report_date.strftime('%d%m%Y')

    # When calling extract_additional_information, pass remedial_works_value as an argument
    additional_info_for_db, additional_info_for_db_secondary = extract_additional_information(text, business_entity, date_str, remedial_works_value)

    print(f"Remedial Actions?:", remedial_works_value)

    info = {
        "Inspection Ref No": f"{business_entity}-PWR-{formatted_date}-{job_no.group(1) if job_no else ''}",
        "Remedial Reference Number": f"{business_entity}-PWR-{formatted_date}-{job_no.group(1) if job_no else ''}-{inspection_no.group(1) if inspection_no else ''}",
        "Action Owner": "NSC",
        "Date Action Raised": date.group(1) if date else "",
        "Corrective Job Number": "",
        "Remedial Works Action Required Notes": f"{remedial_works_notes} - Client-ID:{client_id.group(1)}, - Serial Number:{serial_no.group(1)}",
        "Priority": priority,
        "Target Completion Date": target_completion_date,
        "Actual Completion Date": "",
        "PiC Comments": "",
        "Property Inspection Ref No": "",
        "Compliance or Asset Type_External Ref No": f"{business_entity}PWR",
        "Property_Business Entity": business_entity,
    }

    return info

def extract_additional_information(text, business_entity, date_str, remedial_works_value):

    job_no = re.search(r"#JobID#\s*(\d+)", text)
    date_obj = datetime.datetime.strptime(date_str, "%d%m%Y")

    additional_info = {
        "Compliance or Asset Ref No": f"{business_entity}PWR",
        "External Inspection Ref No": f"{business_entity}-PWR-{date_str}-{job_no.group(1) if job_no else ''}",
        "Inspection Date": f"{date_obj.strftime('%d/%m/%Y')}",
        "Contractor": "ISI",
        "Document": f"{business_entity}-PWR-{date_str}.pdf",
        "Remedial Works": remedial_works_value, #Need this to update dynamically
        "Risk Rating": "",
        "Comments": "",
        "Archive": "",
        "Exclude from KPI": "",
        "Inspection Fully Completed": "Yes",
        "Properties_Business Entity": f"{business_entity}",
    }

    # New code to add the second row with headers
    additional_info_secondary = {
        "Compliance or Asset Ref No": "Asset No",
        "External Inspection Ref No": "Inspection Ref / Job No",
        "Inspection Date": "Inspection Date",
        "Contractor": "Contractor",
        "Document": "Document",
        "Remedial Works": "Remedial Works",
        "Risk Rating": "Risk Rating",
        "Comments": "Comments",
        "Archive": "Archive?",
        "Exclude from KPI": "Exclude from KPI",
        "Inspection Fully Completed": "Inspection Fully Completed?",
        "Properties_Business Entity": "Business Entity",
    }

    return additional_info, additional_info_secondary

def process_puwer_documents(input_folder, output_folder, processed_folder, business_entity, get_db, invoice_group, invoice_value):

    processed_pdfs = []
    faulty_reports_pdfs = []
    first_report_date = None
    additional_info_for_db = None

    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            text = extract_text_from_pdf(pdf_path)

            if "#JobType# PUWER" in text or "#JobType# SkippedInspection" in text:
                information = extract_information(text, business_entity)

                if information["Remedial Works Action Required Notes"].strip().lower() == "none":
                    faulty_reports_pdfs.append(pdf_path)
                    continue

                if first_report_date is None:
                    date_match = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)
                    if date_match:
                        first_report_date = datetime.datetime.strptime(date_match.group(1), "%d/%m/%Y")

                if additional_info_for_db is None:
                    remedial_works_value = "No"
                    additional_info_for_db = extract_additional_information(text, business_entity, first_report_date.strftime('%d%m%Y'), remedial_works_value)

                processed_pdfs.append(pdf_path)
            else:
                faulty_reports_pdfs.append(pdf_path)  # Move faulty reports PDF


    main_merged_pdf_path = os.path.join(output_folder, f"{business_entity}-PWR-{first_report_date.strftime('%d%m%Y')}.pdf")
    faulty_reports_path = os.path.join(output_folder, f"{business_entity}-FAULTYREPORTS-{first_report_date.strftime('%d%m%Y')}.pdf")

    merge_pdfs(processed_pdfs, main_merged_pdf_path)

    if faulty_reports_pdfs:
        merge_pdfs(faulty_reports_pdfs, faulty_reports_path)

    date_str = first_report_date.strftime('%d%m%Y')

    csv_file = os.path.join(output_folder, f"{business_entity}-PWR-{date_str}-REMEDIALACTIONS.csv")
    csv_additional_file = os.path.join(output_folder, f"{business_entity}-PWR-{date_str}.csv")

    header = ["Inspection Ref No", "Remedial Reference Number", "Action Owner", "Date Action Raised", "Corrective Job Number", "Remedial Works Action Required Notes", "Priority", "Target Completion Date", "Actual Completion Date", "PiC Comments", "Property Inspection Ref No", "Compliance or Asset Type_External Ref No", "Property_Business Entity"]

    # Define the secondary header for the main CSV file
    secondary_header_main = [
        "Inspection Ref / Job No",
        "Remedial Reference Number",
        "Action Owner",
        "Date Action Raised",
        "Corrective Job Number",
        "Remedial Works Action Required/Notes",
        "Priority",
        "Target Completion Date",
        "Actual Completion Date",
        "PiC Comments",
        "Property Inspection Ref. No.",
        "Asset No",
        "Business Entity",
    ]

    # Define the secondary header for the additional CSV file
    secondary_header_additional = [
        "Compliance or Asset Ref No",
        "External Inspection Ref No",
        "Inspection Date",
        "Contractor",
        "Document",
        "Remedial Works",
        "Risk Rating",
        "Comments",
        "Archive",
        "Exclude from KPI",
        "Inspection Fully Completed",
        "Properties_Business Entity",
    ]

    with open(csv_file, "w", newline='', encoding='utf-8') as csvfile, open(csv_additional_file, "w", newline='', encoding='utf-8') as csv_additionalfile:
        csvwriter = csv.writer(csvfile)
        csv_additional_writer = csv.writer(csv_additionalfile)

        # Write the first row of headers for both CSV files
        csvwriter.writerow(header)
        
        # Write the secondary header for the main CSV file
        csvwriter.writerow(secondary_header_main)
        
        # Write the secondary header for the additional CSV file
        csv_additional_writer.writerow(secondary_header_additional)

        # Extract job_no from the Inspection Ref / Job No
        job_no = information["Inspection Ref No"].split("-")[-1]
        
        # Write the second row with additional information for both CSV files
        additional_info, additional_info_secondary = extract_additional_information(text, business_entity, date_str, remedial_works_value)
        csv_additional_writer.writerow(additional_info_secondary.values())

        csv_additional_writer.writerow(additional_info.values())

        for pdf_path in processed_pdfs:
            text = extract_text_from_pdf(pdf_path)
            information = extract_information(text, business_entity)
            if information["Priority"] in ["Intolerable", "Substantial", "Moderate"]:
                row = [information[key] for key in header]
                csvwriter.writerow(row)

                # Move the db_insert_function call here to ensure 'information' is defined
                if additional_info_for_db is not None:
                    db_insert_function(information, get_db)


    # Call process_report_entry here to ensure it's only called once
    process_report_entry(information, additional_info_for_db, invoice_value, invoice_group, get_db)

    return main_merged_pdf_path, faulty_reports_path, csv_file, csv_additional_file, first_report_date, date_str, additional_info_for_db



def db_insert_function(info, get_db):
    conn = get_db()
    try:
        if isinstance(info, dict):

            logged_user = f"{current_user.first_name} {current_user.second_name}"

            inspection_data = (
                info.get("Inspection Ref No", ""),
                info.get("Remedial Reference Number", ""),
                info.get("Action Owner", ""),
                info.get("Date Action Raised", ""),
                info.get("Corrective Job Number", ""),
                info.get("Remedial Works Action Required Notes", ""),
                info.get("Priority", ""),
                info.get("Target Completion Date", ""),
                info.get("Actual Completion Date", ""),
                info.get("Property Inspection Ref No", ""),
                info.get("Compliance or Asset Type_External Ref No", ""),
                info.get("Property_Business Entity", ""),
                logged_user
            )

            # Insert inspection data into 'aecom_inspection' table
            print("Inserting into aecom_inspection")
            conn.execute('''
                INSERT INTO aecom_inspection 
                (inspection_ref, remedial_reference_number, action_owner, data_action_raised, 
                corrective_job_number, actions_required, priority, target_completion_date, 
                actual_completion_date, property_inspection_reference, asset_no, business_entity, logged_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', inspection_data)

        else:
            print("Error: 'info' object is not a dictionary.")

        conn.commit()  # Commit changes here
    except Exception as e:
        print(f"Error inserting data into database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()



def process_report_entry(info, additional_info, invoice_value, invoice_group, get_db):
    conn = get_db()
    try:
        if isinstance(additional_info, tuple) and len(additional_info) == 2 and isinstance(additional_info[0], dict):

            zipname = f"{additional_info[0].get('Properties_Business Entity', '')}_output.zip"
            process_date = datetime.datetime.now().strftime("%d/%m/%Y")
            logged_user = f"{current_user.first_name} {current_user.second_name}"


            report_data = (
                additional_info[0].get("External Inspection Ref No", ""),
                additional_info[0].get("Inspection Date", ""),
                process_date,
                additional_info[0].get("Document", ""),
                zipname,
                additional_info[0].get("Properties_Business Entity", ""),
                invoice_value,
                invoice_group,
                logged_user
            )


            visit_data = (
                info.get("Asset No", ""),
                additional_info[0].get("External Inspection Ref No", ""),
                additional_info[0].get("Inspection Date", ""),
                additional_info[0].get("Contractor", ""),
                additional_info[0].get("Document", ""),
                additional_info[0].get("Remedial Works", ""),
                additional_info[0].get("Risk Rating", ""),
                additional_info[0].get("Comments", ""),
                additional_info[0].get("Archive", ""),
                additional_info[0].get("Exclude from KPI", ""),
                additional_info[0].get("Inspection Fully Completed", ""),
                additional_info[0].get("Properties_Business Entity", ""),
                logged_user
            )

            # Insert report data into 'aecom_reports' table
            print(len(report_data))
            print(len(visit_data))

            print("Inserting into aecom_reports")
            conn.execute('''
                INSERT INTO aecom_reports 
                (inspection_ref, inspection_date, process_date, document_name, zipname, business_entity, invoice_value, invoice_group, logged_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', report_data)



            # Insert visit data into 'aecom_visits' table
            print("Inserting into aecom_visits")

            conn.execute('''
                INSERT INTO aecom_visits 
                (asset_no, inspection_ref, inspection_date, contractor, document, 
                remedial_actions, risk_rating, comments, archive, exclude_from_kpi, 
                inspection_fully_complete, business_entity, logged_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', visit_data)


            conn.commit()

        else:
            print("Error: Report data is broken or not present.")
    except Exception as e:
        print(f"Error inserting data into database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()


# Generate a unique filename (from lolerextract.py)
def generate_unique_filename(client_name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H")
    filename = f"{client_name}_{timestamp}.csv"
    return filename

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text(x_tolerance=2)
    return text

def merge_pdfs(pdf_files, output_path):
    merger = PdfMerger()
    for pdf in pdf_files:
        with open(pdf, "rb") as pdf_file:
            merger.append(pdf_file)
    with open(output_path, "wb") as merged_pdf:
        merger.write(merged_pdf)

@aecom_blueprint.route('/delete-record-aecom', methods=['POST'])
@login_required
def delete_record_aecom():
    aecom_report_id = request.form.get('id')
    conn = get_db()
    try:
        # Get the file name associated with the record
        cursor = conn.execute('SELECT zipname FROM aecom_reports WHERE id = ?', (aecom_report_id,))
        result = cursor.fetchone()
        
        if result:
            file_name = result['zipname']

            # Delete the file associated with the record
            file_path = os.path.join(OUTPUT_FOLDER, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        # Delete the record from the database
        conn.execute('DELETE FROM aecom_reports WHERE id = ?', (aecom_report_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Record successfully deleted.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting Record: {e}'}), 500
    finally:
        conn.close()

# Function to add sites from CSV to SQLite database
def add_sites_from_csv(csv_file, db_file, table_name):
    conn = get_db()
    cursor = conn.cursor()

    with open(csv_file, 'r', newline='', encoding='latin-1') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            values = (row['account_no'], row['location_name'], row['business_entity'], row['postcode'],
                      row['address_line_1'], row['address_line_2'], row['town_city'], row['logged_by'])
            cursor.execute(f'''
                INSERT INTO {table_name} (account_no, location_name, business_entity, postcode,
                                          address_line_1, address_line_2, town_city, logged_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)

    conn.commit()
    conn.close()

# Route to handle CSV file upload
@aecom_blueprint.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})

        file = request.files['file']

        # If user does not select a file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})

        # Check if the file is CSV
        if file and file.filename.endswith('.csv'):
            # Save the uploaded file to a temporary location
            file_path = 'temp.csv'
            file.save(file_path)

            # Add sites from CSV to database
            add_sites_from_csv(file_path, 'your_database.db', 'aecom_sites')

            # Remove the temporary file
            os.remove(file_path)

            return jsonify({'success': True, 'message': 'CSV file uploaded successfully'})

        else:
            return jsonify({'success': False, 'message': 'Please upload a CSV file'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@aecom_blueprint.route('/download_file/<filename>')
@login_required
def download_file(filename):
    # Ensure OUTPUT_FOLDER is correctly set to the directory containing the generated CSV
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


def calculate_average_processing_time(get_db):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Query the database to fetch inspection_date and process_date
        cursor.execute("SELECT inspection_date, process_date FROM aecom_reports")
        rows = cursor.fetchall()

        total_time = datetime.timedelta(0)
        total_reports = len(rows)

        for row in rows:
            inspection_date = datetime.datetime.strptime(row['inspection_date'], "%d/%m/%Y")
            process_date = datetime.datetime.strptime(row['process_date'], "%d/%m/%Y")
            time_difference = process_date - inspection_date
            total_time += time_difference

        # Calculate the average processing time
        if total_reports > 0:
            average_time = total_time / total_reports
        else:
            average_time = datetime.timedelta(0)

        return average_time
    except Exception as e:
        print(f"Error calculating average processing time: {str(e)}")
        return None
    finally:
        conn.close()
