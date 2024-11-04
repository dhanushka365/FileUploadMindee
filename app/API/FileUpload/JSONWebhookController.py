import os
import requests
from flask_apispec import doc, use_kwargs
from flask_apispec.views import MethodResource
from flask_restful import Resource
from marshmallow import Schema, fields
from flask import request

# Schema for JSON object request
class JSONRequestSchema(Schema):
    access_key = fields.Str(required=True, description="Access key for the request")
    email = fields.Email(required=True, description="User's email")
    fault_detail = fields.Str(required=True, description="Details of the fault")
    instruction_notes = fields.Str(required=True, description="Instruction notes")
    paymentbillingname = fields.Str(required=True, description="Billing name for payment")
    paymentcompanyname = fields.Str(description="Company name for payment")
    paymentponumber = fields.Str(description="Purchase order number")
    propertymanagerdetails = fields.Dict(required=True, description="Property manager details")
    shippingcity = fields.Str(required=True, description="City for shipping")
    shippingemail = fields.Email(required=True, description="Email for shipping")
    shippingname = fields.Str(required=True, description="Name for shipping")
    shippingphone = fields.Str(required=True, description="Phone number for shipping")
    shippingpostalcode = fields.Str(required=True, description="Postal code for shipping")
    shippingstreet = fields.Str(required=True, description="Street address for shipping")
    type = fields.Str(required=True, description="Type of request")
    file_path = fields.Str(required=True, description="Path of the file associated with the request")

# Controller for JSON object submission
class JSONWebhookController(MethodResource, Resource):
    @doc(description='This API accepts a JSON object and forwards it to a webhook', tags=['JSON Webhook'])
    @use_kwargs(JSONRequestSchema, location='json')  # 'json' specifies the body should be JSON
    def post(self, **json_data):
        """
        Post method for JSON object submission.
        Accepts a JSON payload, processes it, and forwards it to the webhook.
        """
        webhook_url = "https://dev.smarterappliances.co.uk/Clientresponse/testWorkorders"

        try:
            # Send the JSON data to the webhook
            response = requests.post(webhook_url, json=json_data)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Return the webhook response for verification
            return {
                'message': 'Data successfully forwarded to webhook',
                'webhook_response': response.json()  # Return the response from the webhook
            }, 200

        except requests.RequestException as e:
            # Handle the case where the webhook request fails
            return {
                'message': 'Failed to send data to webhook',
                'error': str(e)
            }, 500
