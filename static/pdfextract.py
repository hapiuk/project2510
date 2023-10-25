import os
import re
import pdfplumber
import csv
import gc
import shutil
import time
import argparse
import datetime
from tqdm import tqdm
from PyPDF2 import PdfMerger
import zipfile


def merge_pdfs(pdf_files, output_path):
    merger = PdfMerger()
    for pdf in pdf_files:
        with open(pdf, "rb") as pdf_file:
            merger.append(pdf_file)
    with open(output_path, "wb") as merged_pdf:
        merger.write(merged_pdf)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text(x_tolerance=2)
    return text

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

def extract_additional_information(text, business_entity, date_str):
    job_no = re.search(r"#JobID#\s*(\d+)", text)

    date_obj = datetime.datetime.strptime(date_str, "%d%m%Y")

    additional_info = {
        "Compliance or Asset Ref No": f"{business_entity}PWR",
        "External Inspection Ref No": f"{business_entity}.-PWR-{date_str}-{job_no.group(1) if job_no else ''}",
        "Inspection Date": f"{date_obj.strftime('%d/%m/%Y')}",
        "Contractor": "ISI",
        "Document": f"{business_entity}.-PWR-{date_str}.pdf",
        "Remedial Works": "Yes",
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

def main(input_folder, output_folder, processed_folder, business_entity):
    processed_pdfs = []
    faulty_reports_pdfs = []
    first_report_date = None

    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            text = extract_text_from_pdf(pdf_path)

            if "#JobType# PUWER" in text or "#JobType# SkippedInspection" in text:
                information = extract_information(text, business_entity)

                if information["Remedial Works Action Required Notes"].strip().lower() == "none":
                    faulty_reports_pdfs.append(pdf_path)  # Move faulty reports PDF
                    continue

                if first_report_date is None:
                    date_match = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)
                    if date_match:
                        first_report_date = datetime.datetime.strptime(date_match.group(1), "%d/%m/%Y")

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
        additional_info, additional_info_secondary = extract_additional_information(text, business_entity, date_str)
        csv_additional_writer.writerow(additional_info_secondary.values())

        csv_additional_writer.writerow(additional_info.values())

        for pdf_path in processed_pdfs:
            text = extract_text_from_pdf(pdf_path)
            information = extract_information(text, business_entity)
            if information["Priority"] in ["Intolerable", "Substantial", "Moderate"]:
                row = [information[key] for key in header]
                csvwriter.writerow(row)

    return main_merged_pdf_path, faulty_reports_path, csv_file, csv_additional_file, first_report_date, date_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input folder containing PDF files")
    parser.add_argument("--output", required=True, help="Output folder for generated files")
    parser.add_argument("--processed", required=True, help="Processed folder for completed files")
    parser.add_argument("--business_entity", required=True, help="Business entity for the processing")
    args = parser.parse_args()

    main_merged_pdf_path, faulty_reports_path, csv_file, csv_additional_file, first_report_date, date_str = main(
        args.input, args.output, args.processed, args.business_entity
    )

    print(f"Main merged PDF created: {main_merged_pdf_path}")
    print(f"Faulty Reports PDF created: {faulty_reports_path}")
    print(f"CSV file created: {csv_file}")
    print(f"Additional CSV file created: {csv_additional_file}")
    print(f"First Report Date: {first_report_date}")