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
    import re  # For sanitizing filenames
    from PIL import Image
    import fitz  # PyMuPDF for PDF to image conversion
    from urllib.parse import urljoin  # For creating full URLs
    import openai
    import json

    print("All imports are ok............")
except Exception as e:
    print(f"Error: {e}")

# Base directories
#BASE_DIRECTORY = os.path.join(os.getcwd(), "./app/static/temporary")
BASE_DIRECTORY = os.path.join(os.getcwd(), "./static/temporary")
# Ensure directories exist
os.makedirs(BASE_DIRECTORY, exist_ok=True)


# Marshmallow schema for file upload
class GPTFileUploadSchema(Schema):
    file = fields.Raw(required=True, description="Alan De Maid PDFs File to upload", type="file")


# Utility functions
def get_versioned_filename(directory, filename):
    base, ext = os.path.splitext(filename)
    version = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_v{version}{ext}"
        version += 1
    return new_filename


def save_file(file):
    incoming_folder = os.path.join(BASE_DIRECTORY, 'incoming')
    os.makedirs(incoming_folder, exist_ok=True)
    temp_filename = secure_filename(file.filename)
    file_path = os.path.join(incoming_folder, temp_filename)
    file.save(file_path)
    return file_path


def move_file_to_company_folder(temp_file_path, company_name, new_filename):
    company_folder = os.path.join(BASE_DIRECTORY, company_name)
    os.makedirs(company_folder, exist_ok=True)
    new_filename = secure_filename(f"{company_name}_{new_filename}.pdf")
    new_filename = get_versioned_filename(company_folder, new_filename)
    new_file_path = os.path.join(company_folder, new_filename)
    os.rename(temp_file_path, new_file_path)
    return new_file_path


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def extract_info_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        for keyword in KEYWORDS:
            if keyword.lower() in text.lower():
                return secure_filename(keyword)
        return "not found"


def generate_json_from_text(api_key, input_text):
    # Set the OpenAI API key
    openai.api_key = api_key

    # ChatGPT prompt to extract and format data
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts structured data from unstructured text. "
                "Your task is to extract relevant details and format them as JSON in the specified format. "
                "Here in the final output json 'paymentbillingname' is the landlord's name. "
                "Here in the final output json 'paymentponumber' is the work order number. "
                "Here in the final output json 'shippingcity', 'shippingstreet', and 'shippingpostalcode' are mentioned in the property address. "
                "Here in the final output json 'shippingemail', 'shippingname', and 'shippingphone' provide tenant details. "
                "Here in the final output json 'fault_detail' is a short sentence about the work order. "
                "Here in the final output json 'instruction_notes' is a detailed description of the work order, including the issue"
                "what to do, customer wishes, and any special notes or prices. "
                "please don't extract smarter appliances LTD related emails as 'shipppingemail' , 'paymentbuyeremail' or 'email'"
                "please don't use this data in my final response they are smarter appliances LTD related details  Smarter Appliances Ltd Smarter Appliances Ltd 136-137, High Street Ilfracombe EX34 9EZ"
                "Here in the final output json 'shippingcompanyname' should be the company name for billing if applicable. "
                "Here in the final output json 'type' indicates whether the work order is a repair or a replacement. Always in the final json response type should contain the only repair or replacement according to the work order type "
                "In BASE PROPERTY SPECIALISTS LTD work orders  'Problem reported' is the place to extract details for 'fault_detail' and the 'Description' is the place to extract details for 'instruction_notes' "
                "Here in the final output json 'propertymanagerdetails' contains the details of the work manager or the person who instructed the work order."
                "Here in the final output json 'access_key' means how to get access to the property. It might be via tenant. Like wise if some one need to reach the fault device some time he need to get access to the property. that details should be come here. If its tenant give me a answer like tenant"
            ),
        },
        {
            "role": "user",
            "content": f"""
            Extract the relevant details from the following text and return a JSON response in the specified format:
            {{
              "access_key": "",
              "email": "",
              "fault_detail": "",
              "instruction_notes": "",
              "paymentbillingname": "",
              "paymentcompanyname": "",
              "paymentponumber": "",
              "propertymanagerdetails": {{
                "payment_buyer_name": "",
                "paymentbuyeremail": "",
                "paymentbyerphone": ""
              }},
              "shippingcity": "",
              "shippingemail": "",
              "shippingname": "",
              "shippingphone": "",
              "shippingpostalcode": "",
              "shippingstreet": "",
              "type": "",
              "shippingcompanyname": ""
            }}
            
            Text:
            {input_text}
            
            Ensure all details are filled correctly based on the provided text. Provide the JSON output only.
            """
        }
    ]

    try:
        # Send request to the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0
        )

        # Extract the JSON-like response from the assistant's reply
        assistant_message = response['choices'][0]['message']['content']

        # Parse the extracted JSON response
        json_response = json.loads(assistant_message)

        return json_response

    except json.JSONDecodeError:
        print("Failed to parse JSON from the response. Ensure the model output is valid JSON.")
        return None
    except Exception as w:
        print(f"An error occurred: {w}")
        return None


def extract_text_with_pymupdf(pdf_path):
    try:
        doc1 = fitz.open(pdf_path)
        text = ""
        for page in doc1:
            text += page.get_text()
        return text.strip()
    except Exception as q:
        return f"An error occurred: {q}"


# Flask API Controller
class GPTFileUploadController(MethodResource, Resource):
    @doc(description='Light GPT PDFs Upload endpoint', tags=['Light GPT PDFs Endpoint'])
    @use_kwargs(GPTFileUploadSchema, location='files')
    def post(self, file):
        global response, json_content, final_file_path
        if not file:
            return {'message': 'No file part'}, 400
        if file.filename == '':
            return {'message': 'No selected file'}, 400
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            return {'message': 'Only PDF files are allowed.'}, 400
        try:
            temp_file_path = save_file(file)
            company_name = extract_info_from_pdf(temp_file_path)
            if company_name == "not found":
                return {'message': 'No valid company name found in the PDF'}, 400

            final_file_path = move_file_to_company_folder(temp_file_path, company_name, "processed")
            extracted_texts = extract_text_with_pymupdf(final_file_path)

            result = generate_json_from_text(api_key, extracted_texts)

            # Construct accessible URLs
            base_url = urljoin(request.host_url, "temporary/")  # Add '/temporary/' after the host
            file_url = urljoin(base_url, os.path.relpath(final_file_path, BASE_DIRECTORY))
            result['file_path'] = file_url
            webhook_url = "https://dev.smarterappliances.co.uk/Clientresponse/testWorkorders"
            try:
                response = requests.post(webhook_url, json=result)
                json_content = response.json()
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Failed to send webhook: {e}")

            return {
                'result': json_content
            }, 201

        except Exception as e:
            if final_file_path  and os.path.exists(final_file_path ):
                os.remove(final_file_path )
            return {'message': 'Failed to process file with GPT', 'error': str(e)}, 500


# Company keywords
KEYWORDS = [
    "Benham", "CBRE", "Chestertons", "Cluttons", "GCP", "Haart", "Hamptons", "KFH",
    "marshandparsons", "MyLako", "Savills", "Squires", "APW", "winkworth", "Streets Ahead",
    "metro-village", "alandemaid", "bairstoweves", "gpees", "Mann", "LCP", "Foxtons",
    "Cole", "Chase Buchanan’s", "Featherstone"
]
