try:
    import os
    import pdfplumber
    import requests
    from flask_apispec import doc, use_kwargs
    from flask_apispec.views import MethodResource
    from flask_restful import Resource
    from marshmallow import Schema, fields
    from werkzeug.utils import secure_filename
    from flask import request, jsonify

    print("All imports are ok............")
except Exception as e:
    print(f"Error: {e}")

# Define the base directory where files will be uploaded
BASE_DIRECTORY = os.path.join(os.getcwd(), "./app/static/temporary") # in server place remove app
#BASE_DIRECTORY = os.path.join(os.getcwd(), "./static/temporary") # in server place remove app

# Ensure the base directory exists
if not os.path.exists(BASE_DIRECTORY):
    os.makedirs(BASE_DIRECTORY)

class AlanDeMaidFileUploadSchema(Schema):
    file = fields.Raw(required=True, description="Alan De Maid PDFs File to upload", type="file")

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

class AlanDeMaidFileUploadController(MethodResource, Resource):
    @doc(description='Alan De Maid PDFs Upload endpoint', tags=['Alan De Maid PDFs  Endpoint'])
    @use_kwargs(AlanDeMaidFileUploadSchema, location='files')  # 'files' is used for file uploads
    def post(self, file):
        """
                Post method for file uploads. Saves the file and returns the file path.
                """
        global response, json_content
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


            return {
                # 'result': json_content
                'result': "cleaned_data"
            }, 201

        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return {'message': 'Failed to process file with Mindee', 'error': str(e)}, 500

    KEYWORDS = [
        "Benham", "CBRE", "Chestertons", "Cluttons",
        "GCP", "Haart", "Hamptons", "KFH", "marshandparsons", "MyLako",
        "Savills", "Squires", "APW", "winkworth", "Streets Ahead", "metro-village",
        "alandemaid", "bairstoweves", "gpees", "Mann",
        "LCP", "Foxtons", "Cole", "Chase Buchanan’s", "Featherstone"
    ]
