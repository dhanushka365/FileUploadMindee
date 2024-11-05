import os
import requests
from flask_apispec import doc
from flask_apispec.views import MethodResource
from flask_restful import Resource
from flask import request, jsonify
import logging


# Controller for JSON object submission
class JSONWebhookController(MethodResource, Resource):
    @doc(description='This API accepts a JSON object and forwards it to a webhook', tags=['JSON Webhook'])
    def post(self):
        """
        Post method for JSON object submission.
        Accepts a JSON payload, processes it, and forwards it to the webhook.
        """
        # Get the incoming JSON data directly from the request
        json_data = request.get_json()

        # Log the received data for debugging
        logging.info(f"Received data: {json_data}")

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