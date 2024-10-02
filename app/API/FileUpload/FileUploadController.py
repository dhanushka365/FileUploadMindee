try:
    import os
    import tempfile
    from flask import Flask
    from flask_restful import Resource, Api
    from apispec import APISpec
    from marshmallow import Schema, fields
    from apispec.ext.marshmallow import MarshmallowPlugin
    from flask_apispec.extension import FlaskApiSpec
    from flask_apispec.views import MethodResource
    from flask_apispec import marshal_with, doc, use_kwargs

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
            return {'message': 'No file provided'}, 400

        file_name = file.filename
        file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

        try:
            # Save the file to the upload directory
            file.save(file_path)
            print(f"File saved to: {file_path}")

            # Return the file path in the response
            return {
                'message': 'File uploaded successfully',
                'file_path': file_path
            }, 201

        except Exception as e:
            return {'message': 'Failed to save file', 'error': str(e)}, 500