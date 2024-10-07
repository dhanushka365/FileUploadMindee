

try:
    import os
    import tempfile
    from flask import Flask, jsonify
    from flask_restful import Resource, Api
    from apispec import APISpec
    from marshmallow import Schema, fields
    from apispec.ext.marshmallow import MarshmallowPlugin
    from flask_apispec.extension import FlaskApiSpec
    from flask_apispec.views import MethodResource
    from flask_apispec import marshal_with, doc, use_kwargs
    from werkzeug.utils import secure_filename
    from mindee import Client, AsyncPredictResponse, product
    import json
    import pdfplumber
    print("All imports are ok............")
except Exception as e:
    print("Error: {} ".format(e))

# Define the upload directory
UPLOAD_DIRECTORY = os.path.join(os.getcwd(), "uploads")

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Schema for file upload request
class FileUploadSchema(Schema):
    file = fields.Raw(required=True, description="File to upload", type="file")


# Controller for File Upload
class FileUploadController(MethodResource, Resource):
    @doc(description='This API allows file uploads and returns the file save path', tags=['File Upload'])
    @use_kwargs(FileUploadSchema, location='files')  # 'files' is used for file uploads
    def post(self, file):
        """
        Post method for file uploads. Saves the file and returns the file path.
        """
        if not file:
            return {'message': 'No file part'}, 400

        file_name = file.filename
        if file.filename == '':
            return {'message': 'No selected file'}, 400

        # Ensure the file is a PDF
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            return {'message': 'Only PDF files are allowed.'}, 400

        file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

        try:
            # Save the file to the upload directory
            file.save(file_path)
            print(f"File saved to: {file_path}")

            # Use the utility function to extract the filename
            extracted_filename = extract_filename_from_pdf(file_path)
            print(f"Extracted filename: {extracted_filename}")


            # Init a new client
            mindee_client = Client(api_key="e0611a74d21d266a82f538946afccd3d")

            # Set up logic based on the extracted filename
            if extracted_filename == 'Benham':
                # Add endpoint for Benham&Reeves
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="benhamreeves_repair",
                    version="1"
                )
            elif extracted_filename == 'CBRE':
                # Add endpoint for CBRE
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="cbre_repair",
                    version="1"
                )
            elif extracted_filename == 'Chestertons':
                # Add endpoint for Chestertons
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="chestertons_repair",
                    version="1"
                )
            elif extracted_filename == 'Cluttons':
                # Add endpoint for Cluttons
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="cluttons_repair",
                    version="1"
                )
            elif extracted_filename == 'Countrywide':
                # Add endpoint for Countrywide
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="countrywide_repair",
                    version="1"
                )
            elif extracted_filename == 'GCP':
                # Add endpoint for GCP
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="gcp_repair",
                    version="1"
                )
            elif extracted_filename == 'Haart':
                # Add endpoint for Haart
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="haart_replacement",
                    version="1"
                )
            elif extracted_filename == 'Hamptons':
                # Add endpoint for Hamptons
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="hamptons_repair",
                    version="1"
                )
            elif extracted_filename == 'KFH':
                # Add endpoint for KFH
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="kfh_repair",
                    version="1"
                )
            elif extracted_filename == 'marshandparsons':
                # Add endpoint for Mash and Parson
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="mash_and_parson_replacement",
                    version="1"
                )
            elif extracted_filename == 'MyLako':
                # Add endpoint for MyLako
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="mylako_repair",
                    version="1"
                )
            elif extracted_filename == 'Savills':
                # Add endpoint for Savills Picture House
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="savills_picture_house_repair",
                    version="1"
                )
            elif extracted_filename == 'Squires':
                # Add endpoint for Squires Estates
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="squires_estates_repair",
                    version="1"
                )
            elif extracted_filename == 'winkworth':
                # Add endpoint for Squires Estates
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="winkworth_repairs",
                    version="1"
                )
            elif extracted_filename == 'Streets Ahead':
                # Add endpoint for Squires Estates
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="streets_ahead_repair",
                    version="1"
                )
            elif extracted_filename == 'metro-village':
                # Add endpoint for Squires Estates
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="metro_village_repair",
                    version="1"
                )
            elif extracted_filename == 'metro-village':
                # Add endpoint for Squires Estates
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="base_property_repair",
                    version="1"
                )
            elif extracted_filename == 'APW':
                # Add endpoint for Squires Estates
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="apw_repair",
                    version="1"
                )
            else:
                # Fallback if no specific match is found
                my_endpoint = mindee_client.create_endpoint(
                    account_name="SmarterDev",
                    endpoint_name="commonworkorder_new",
                    version="1"
                )

            input_doc = mindee_client.source_from_path(file_path)

            result: AsyncPredictResponse = mindee_client.enqueue_and_parse(
                product.GeneratedV1,
                input_doc,
                endpoint=my_endpoint
            )

            # Assuming you have your result from Mindee
            mindee_data = result.document.inference.prediction.fields

            def extract_field_value(field):
                field_type = type(field)
                if "StringField" in str(field_type):
                    return field.value  # Directly return the string value
                elif "GeneratedListField" in str(field_type):
                    return [extract_field_value(item) for item in field.values]  # Handle list fields
                elif "GeneratedObjectField" in str(field_type):
                    # Remove unwanted fields from the object
                    return {
                        key: extract_field_value(getattr(field, key)) for key in dir(field)
                        if
                        not key.startswith('__') and key not in ['page_id', '_GeneratedObjectField__printable_values',
                                                                 '_str_level']
                    }
                else:
                    return str(field)

            cleaned_data = {key: extract_field_value(value) for key, value in mindee_data.items()}

            mindee_data_string = json.dumps(cleaned_data, indent=4)

            print(type(mindee_data_string))

            if os.path.exists(file_path):
                os.remove(file_path)  # Remove the file to save server storage

            return {
                'message': 'File uploaded and processed successfully',
                'result': json.loads(mindee_data_string)
            }, 201

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)  # Remove the file if processing fails
            return {'message': 'Failed to process file with Mindee', 'error': str(e)}, 500



KEYWORDS = [
    "Benham", "CBRE", "Chestertons", "Cluttons", "Countrywide",
    "GCP", "Haart", "Hamptons", "KFH", "marshandparsons", "MyLako",
    "Savills", "Squires", "APW", "winkworth", "Streets Ahead", "metro-village",
]
def extract_filename_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

        for keyword in KEYWORDS:
            if keyword.lower() in text.lower():
                print(f"Keyword found: {keyword}")
                return secure_filename(keyword)

        print("No keyword found.")
        return "not found"