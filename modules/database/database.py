from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime

db_blueprint = Blueprint('db_blueprint', __name__)

DATABASE = './static/isitools.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_user_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            second_name TEXT,
            email_address TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def create_aecom_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aecom_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_ref TEXT,
            inspection_date DATE,
            process_date DATE,
            document_name TEXT,
            zipname TEXT,
            business_entity TEXT,
            invoice_value TEXT,
            invoice_group TEXT,
            logged_by TEXT,
            FOREIGN KEY (business_entity) REFERENCES aecom_sites(business_entity)
        )
    ''')
    conn.commit()
    conn.close()

def create_aecom_visit_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aecom_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_no TEXT,
            inspection_ref TEXT,
            inspection_date DATE,
            contractor TEXT,
            document TEXT,
            remedial_actions TEXT,
            risk_rating TEXT,
            comments TEXT,
            archive TEXT,
            exclude_from_kpi TEXT,
            inspection_fully_complete TEXT,
            business_entity TEXT,
            logged_by TEXT,
            FOREIGN KEY (business_entity) REFERENCES aecom_sites(business_entity)
        )
    ''')
    conn.commit()
    conn.close()

def create_aecom_inspection_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aecom_inspection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_ref TEXT,
            remedial_reference_number TEXT,
            action_owner TEXT,
            data_action_raised DATE,
            corrective_job_number TEXT,
            actions_required TEXT,
            client_id TEXT,
            serial_number TEXT,
            sub_location TEXT,
            priority TEXT,
            target_completion_date DATE,
            actual_completion_date DATE,
            property_inspection_reference TEXT,
            asset_no TEXT,
            business_entity TEXT,
            logged_by TEXT,
            FOREIGN KEY (business_entity) REFERENCES aecom_sites(business_entity)
        )
    ''')
    conn.commit()
    conn.close()

def create_aecom_site_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aecom_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no TEXT,
            location_name TEXT,
            business_entity TEXT,
            postcode TEXT,
            address_line_1 TEXT,
            address_line_2 TEXT,
            town_city TEXT,
            logged_by TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_loler_inspections_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS loler_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            report_date TEXT,
            next_inspection_date TEXT,
            file_name TEXT,
            report_count INTEGER,
            process_date DATE,
            logged_by TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_loler_defects_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS loler_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            equipment_type TEXT,
            isi_number TEXT,
            serial_number TEXT,
            date_of_manufacture TEXT,
            safe_working_load TEXT,
            client_id TEXT,
            sub_location TEXT,
            loler_inspection_id INTEGER,  -- This is the new column
            report_id TEXT,
            a_defect TEXT,
            b_defect TEXT,
            c_defect TEXT,
            d_defect TEXT,
            report_date TEXT,
            next_inspection_date TEXT,
            process_date TEXT,
            logged_by TEXT,
            FOREIGN KEY (loler_inspection_id) REFERENCES loler_inspections(id)  -- Define foreign key constraint
        )
    ''')
    conn.commit()
    conn.close()

create_user_table()
create_aecom_table()
create_aecom_visit_table()
create_aecom_inspection_table()
create_aecom_site_table()
create_loler_inspections_table()
create_loler_defects_table()