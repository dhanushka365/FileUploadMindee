try:
    import cv2
    import numpy as np
    import pytesseract
    import pandas as pd
    import easyocr
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
IMAGE_OUTPUT_DIRECTORY = os.path.join(BASE_DIRECTORY, "Images")
ANNOTATED_IMAGE_OUTPUT_DIRECTORY = os.path.join(BASE_DIRECTORY, "AnnotatedImages")

# Ensure directories exist
os.makedirs(BASE_DIRECTORY, exist_ok=True)
os.makedirs(IMAGE_OUTPUT_DIRECTORY, exist_ok=True)
os.makedirs(ANNOTATED_IMAGE_OUTPUT_DIRECTORY, exist_ok=True)


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


def convert_to_image(temp_file_path):
    pdf_document = fitz.open(temp_file_path)
    pdf_name = sanitize_filename(os.path.splitext(os.path.basename(temp_file_path))[0])
    image_paths = []
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        pix = page.get_pixmap(dpi=350)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img_filename = f"{pdf_name}_page_{page_num + 1}.png"
        img_output_path = os.path.join(IMAGE_OUTPUT_DIRECTORY, img_filename)
        img.save(img_output_path)
        image_paths.append(img_output_path)
    return image_paths


def process_and_save_image(image_path, output_dir):
    try:
        # Load the image
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Convert to grayscale
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        img_thresh = cv2.adaptiveThreshold(
            img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Denoise the image
        img_denoised = cv2.fastNlMeansDenoising(img_thresh, None, 30, 7, 21)

        # Initialize EasyOCR reader
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)  # Disable verbose and GPU if unnecessary

        # Perform OCR
        results = reader.readtext(img_denoised, detail=1)

        # Prepare data for pandas DataFrame
        data_list = []
        extracted_texts = []  # Store only the texts
        for bbox, text, confidence in results:
            (top_left, top_right, bottom_right, bottom_left) = bbox
            x, y = int(top_left[0]), int(top_left[1])
            w, h = int(bottom_right[0] - top_left[0]), int(bottom_right[1] - top_left[1])
            # Clean the text to handle any special characters
            text = text.strip().encode('utf-8', 'ignore').decode('utf-8')
            data_list.append([x, y, w, h, text, confidence])
            extracted_texts.append(text)  # Save text separately

        # Create DataFrame
        df = pd.DataFrame(data_list, columns=['left', 'top', 'width', 'height', 'text', 'confidence'])

        # Annotate the original image
        annotated_image = img_cv.copy()
        for _, row in df.iterrows():
            x, y, w, h, txt = row['left'], row['top'], row['width'], row['height'], row['text']
            cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(annotated_image, txt, (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

        # Save the annotated image
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, "annotated_image.png")
        cv2.imwrite(output_path, annotated_image)

        # Return the annotated image path and extracted texts
        return output_path, extracted_texts

    except Exception as y:
        print(f"An error occurred: {y}")
        return None, None


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
                "Here the 'paymentbillingname' is the landlord's name. "
                "'paymentponumber' is the work order number. "
                "'shippingcity', 'shippingstreet', and 'shippingpostalcode' are mentioned in the property address. "
                "'shippingemail', 'shippingname', and 'shippingphone' provide tenant details. "
                "'fault_detail' is a short sentence about the work order. "
                "'instruction_notes' is a detailed description of the work order, including the issue, "
                "what to do, customer wishes, and any special notes or prices. "
                "'shippingcompanyname' should be the company name for billing if applicable. "
                "'type' indicates whether the work order is a repair or a replacement. "
                "'propertymanagerdetails' contains the details of the work manager or the person who instructed the work order."
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
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Flask API Controller
class GPTFileUploadController(MethodResource, Resource):
    @doc(description='GPT PDFs Upload endpoint', tags=['GPT PDFs Endpoint'])
    @use_kwargs(GPTFileUploadSchema, location='files')
    def post(self, file):
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
            image_paths = convert_to_image(temp_file_path)
            final_file_path = move_file_to_company_folder(temp_file_path, company_name, "processed")
            annotated_image_path, extracted_texts = process_and_save_image(image_paths[0], ANNOTATED_IMAGE_OUTPUT_DIRECTORY)

            result = generate_json_from_text(api_key, extracted_texts)

            # Construct accessible URLs
            base_url = urljoin(request.host_url, "temporary/")  # Add '/temporary/' after the host
            file_url = urljoin(base_url, os.path.relpath(final_file_path, BASE_DIRECTORY))
            annotated_image_url = urljoin(base_url, os.path.relpath(annotated_image_path, BASE_DIRECTORY))
            image_urls = [urljoin(base_url, os.path.relpath(img_path, BASE_DIRECTORY)) for img_path in image_paths]
            result['file_path'] = file_url
            result['annotated_image_path'] = annotated_image_path

            return {
                'result': result
            }, 201
        except Exception as r:
            return {'message': 'Failed to process file', 'error': str(r)}, 500


# Company keywords
KEYWORDS = [
    "Benham", "CBRE", "Chestertons", "Cluttons", "GCP", "Haart", "Hamptons", "KFH",
    "marshandparsons", "MyLako", "Savills", "Squires", "APW", "winkworth", "Streets Ahead",
    "metro-village", "alandemaid", "bairstoweves", "gpees", "Mann", "LCP", "Foxtons",
    "Cole", "Chase Buchanan’s", "Featherstone"
]
