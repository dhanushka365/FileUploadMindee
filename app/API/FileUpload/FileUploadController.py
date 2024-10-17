import os

import pdfplumber
import requests
from flask_apispec import doc, use_kwargs
from flask_apispec.views import MethodResource
from flask_restful import Resource
from marshmallow import Schema, fields
from mindee import Client, product
from werkzeug.utils import secure_filename
from flask import request
# Define the base directory where files will be uploaded
BASE_DIRECTORY = os.path.join(os.getcwd(), "./static/temporary")

# Ensure the base directory exists
if not os.path.exists(BASE_DIRECTORY):
    os.makedirs(BASE_DIRECTORY)

# Schema for file upload request
class FileUploadSchema(Schema):
    file = fields.Raw(required=True, description="File to upload", type="file")

def extract_info_from_pdf(file_path):
    """
    Extracts the company name from the PDF.
    """
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

        # Find the company name
        for keyword in KEYWORDS:
            if keyword.lower() in text.lower():
                return secure_filename(keyword)

        return "not found"


def get_versioned_filename(directory, filename):
    """
    Checks if a file with the same name exists in the directory.
    If it does, append a version number to the filename.
    """
    base, ext = os.path.splitext(filename)
    version = 1
    new_filename = filename

    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_v{version}{ext}"
        version += 1

    return new_filename


def save_file(file):
    """
    Saves the uploaded file in a general 'incoming' folder temporarily.
    """
    # Create the directory for 'incoming' folder inside the 'temporary' directory
    incoming_folder = os.path.join(BASE_DIRECTORY, 'incoming')
    if not os.path.exists(incoming_folder):
        os.makedirs(incoming_folder)

    # Save the file temporarily using the original filename
    temp_filename = secure_filename(file.filename)
    file_path = os.path.join(incoming_folder, temp_filename)
    file.save(file_path)

    return file_path


def move_file_to_company_folder(temp_file_path, company_name, new_filename):
    """
    Moves and renames the file to the correct company folder with a new filename.
    """
    # Create the directory for the company inside the 'temporary' directory
    company_folder = os.path.join(BASE_DIRECTORY, company_name)
    if not os.path.exists(company_folder):
        os.makedirs(company_folder)

    # Generate a secure and versioned filename
    new_filename = secure_filename(f"{company_name}_{new_filename}.pdf")
    new_filename = get_versioned_filename(company_folder, new_filename)

    # Move the file to the company folder
    new_file_path = os.path.join(company_folder, new_filename)
    os.rename(temp_file_path, new_file_path)

    return new_file_path


# Controller for File Upload
class FileUploadController(MethodResource, Resource):
    @doc(description='This API allows file uploads and returns the file save path', tags=['File Upload'])
    @use_kwargs(FileUploadSchema, location='files')  # 'files' is used for file uploads
    def post(self, file):
        """
        Post method for file uploads. Saves the file and returns the file path.
        """
        temp_file_path = None

        if not file:
            return {'message': 'No file part'}, 400

        if file.filename == '':
            return {'message': 'No selected file'}, 400

        # Ensure the file is a PDF
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            return {'message': 'Only PDF files are allowed.'}, 400

        try:
            # Step 1: Save the file temporarily in the 'incoming' folder
            temp_file_path = save_file(file)

            # Step 2: Extract the company name from the PDF
            company_name = extract_info_from_pdf(temp_file_path)
            if company_name == "not found":
                return {'message': 'No valid company found in the PDF'}, 400

            # Step 3: Initialize Mindee Client
            mindee_client = Client(api_key="eed1f2976fcd28860b0e1af3f1d81c1a")

            # Step 4: Set up the Mindee endpoint for the extracted company
            endpoints = {
                "Benham": "benham_repair",
                "CBRE": "cbre_repair",
                "Chestertons": "chestertons_repair",
                "Cluttons": "cluttons_repair",
                "Countrywide": "countrywide_repair",
                "GCP": "gcp_repair",
                "Haart": "haart_replacement",
                "Hamptons": "hamptons_repair",
                "KFH": "kfh_repair",
                "marshandparsons": "mash_and_parson_replacement",
                "MyLako": "mylako_repair",
                "Savills": "savills_picture_house_repair",
                "Squires": "squires_estates_repair",
                "alandemaid": "alan_de_maid",
                "bairstoweves": "bairstow_eves",
                "gpees": "gascoigne_pees",
                "manndartford": "mann",
                "LCP": "lcp",
                "winkworth": "winkworth_repairs",
                "Streets Ahead": "streets_ahead_repair",
                "metro-village": "metro_village_repair",
                "APW": "apw_repair",
            }

            # Default fallback endpoint
            default_endpoint = "commonworkorder_new"
            my_endpoint = mindee_client.create_endpoint(
                account_name="SmarterDev",
                endpoint_name=endpoints.get(company_name, default_endpoint),
                version="1"
            )

            # Step 5: Upload and process the PDF with Mindee
            input_doc = mindee_client.source_from_path(temp_file_path)
            result = mindee_client.enqueue_and_parse(product.GeneratedV1, input_doc, endpoint=my_endpoint)

            # Step 6: Extract and clean data from Mindee result
            mindee_data = result.document.inference.prediction.fields

            def extract_field_value(field):
                field_type = type(field)
                if "StringField" in str(field_type):
                    return field.value
                elif "GeneratedListField" in str(field_type):
                    return [extract_field_value(item) for item in field.values]
                elif "GeneratedObjectField" in str(field_type):
                    return {
                        key: extract_field_value(getattr(field, key)) for key in dir(field)
                        if not key.startswith('__') and key not in ['page_id', '_GeneratedObjectField__printable_values', '_str_level']
                    }
                else:
                    return str(field)

            cleaned_data = {key: extract_field_value(value) for key, value in mindee_data.items()}
            payment_po_number = cleaned_data.get("paymentponumber", "UnknownPO")

            # Step 7: Move and rename the file to the company-specific folder
            final_file_path = move_file_to_company_folder(temp_file_path, company_name, payment_po_number)
            # Construct the full file URL
            # Inside FileUploadController's post method
            host_url = request.host_url  # This will include protocol (http:// or https://) and the domain/port

            # Construct the full file URL
            host_url = request.host_url  # This will include protocol (http:// or https://) and the domain/port
            full_file_url = host_url + "static/temporary/" + company_name + "/" + os.path.basename(final_file_path)

            cleaned_data['file_path'] = full_file_url

            # Step 8: Send webhook with result data
            webhook_url = "https://smarterappliances.co.uk/Clientresponse/testWorkorders"
            try:
                response = requests.post(webhook_url, json=cleaned_data)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Failed to send webhook: {e}")

            return {
                'file_path': full_file_url,
                'message': 'File uploaded and processed successfully',
                'result': cleaned_data
            }, 201

        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {'message': 'Failed to process file with Mindee', 'error': str(e)}, 500


KEYWORDS = [
    "Benham", "CBRE", "Chestertons", "Cluttons", "Countrywide",
    "GCP", "Haart", "Hamptons", "KFH", "marshandparsons", "MyLako",
    "Savills", "Squires", "APW", "winkworth", "Streets Ahead", "metro-village", "alandemaid", "bairstoweves", "gpees", "manndartford", "LCP",
]
