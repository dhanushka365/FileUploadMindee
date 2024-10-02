try:
    from flask import Flask
    from flask_restful import Api
    from apispec import APISpec
    from marshmallow import Schema, fields
    from apispec.ext.marshmallow import MarshmallowPlugin
    from flask_apispec.extension import FlaskApiSpec
    from flask_apispec import marshal_with, doc, use_kwargs
    from dotenv import load_dotenv

    # Import your controllers
    from API.ClusterHealth.HealthCheckController import HeathController
    from API.FileUpload.FileUploadController import FileUploadController

except Exception as e:
    print("__init__ Modules are Missing: {}".format(e))

# Load environment variables from dev.env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
api = Api(app)

# Configure API specifications
app.config.update({
    'APISPEC_SPEC': APISpec(
        title='Mindee Work Order details Extract Project',
        version='v1',
        plugins=[MarshmallowPlugin()],
        openapi_version='2.0.0'
    ),
    'APISPEC_SWAGGER_URL': '/swagger/',  # URI to access API Doc JSON
    'APISPEC_SWAGGER_UI_URL': '/swagger-ui/'  # URI to access UI of API Doc
})

# Initialize Flask API documentation
docs = FlaskApiSpec(app)

# Register resources
try:
    api.add_resource(HeathController, '/health_check')
    docs.register(HeathController)

    api.add_resource(FileUploadController, '/upload')
    docs.register(FileUploadController)

except Exception as e:
    print("Modules are Missing: {}".format(e))

# Run the Flask app in debug mode
if __name__ == '__main__':
    app.run(debug=True)
