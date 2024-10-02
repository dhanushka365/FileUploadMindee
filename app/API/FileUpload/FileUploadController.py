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
            # Init a new client
            mindee_client = Client(api_key="e0611a74d21d266a82f538946afccd3d")

            # Add the corresponding endpoint (document). Set the account_name to "mindee" if you are using OTS.
            my_endpoint = mindee_client.create_endpoint(
                account_name="SmarterDev",
                endpoint_name="benhamreeves_repair",
                version="1"
            )

            # Load a file from disk
            input_doc = mindee_client.source_from_path(file_path)

            # Parse the file.
            # The endpoint must be specified since it cannot be determined from the class.
            result: AsyncPredictResponse = mindee_client.enqueue_and_parse(
                product.GeneratedV1,
                input_doc,
                endpoint=my_endpoint
            )

            # Assuming you have your result from Mindee
            mindee_data = result.document.inference.prediction.fields

            # Function to extract values from Mindee fields
            def extract_field_value(field):
                # Check the type of the field dynamically
                field_type = type(field)

                if "StringField" in str(field_type):
                    return field.value  # Directly return the string value
                elif "GeneratedListField" in str(field_type):
                    # If it's a list, use a method to get the items instead of accessing 'value'
                    return [extract_field_value(item) for item in field.values]  # Use items or similar method
                elif "GeneratedObjectField" in str(field_type):
                    # Access fields as attributes or another structure
                    return {key: extract_field_value(getattr(field, key)) for key in dir(field) if
                            not key.startswith('__')}
                else:
                    return str(field)  # Fallback for unexpected types

            # Create a cleaned dictionary with extracted values
            cleaned_data = {key: extract_field_value(value) for key, value in mindee_data.items()}

            # Convert cleaned_data to a JSON string with pretty print
            mindee_data_string = json.dumps(cleaned_data, indent=4)

            # Output the cleaned JSON string
            print(mindee_data_string)


            return {
                'message': 'File uploaded and processed successfully',
                'result': mindee_data_string
            }, 201

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)  # Remove the file if processing fails
            return {'message': 'Failed to process file with Mindee', 'error': str(e)}, 500

