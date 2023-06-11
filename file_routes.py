from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import PyPDF2
from docx import Document
import pandas as pd
from dotenv import load_dotenv
from model_training import train_model
from flask import current_app as app
from database import Database
from gridfs import GridFS
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import BytesIO
import datetime
import io

load_dotenv()

file_routes = Blueprint('file_routes', __name__)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Connect to MongoDB and initialize GridFS
client = MongoClient(os.getenv("MONGODB_URI"))
gridfs_db = client.ai_app_db  # Replace 'ai_app_db' with your actual MongoDB database name
fs = GridFS(gridfs_db)

db = Database()

def extract_text_from_pdf(file_content):
    pdf_file = io.BytesIO(file_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file) # use PdfReader instead of PdfFileReader
    text = ""
    for page in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page].extract_text()
    return text

def extract_text_from_docx(file_content):
    docx_file = BytesIO(file_content)
    document = Document(docx_file)
    text = ' '.join([paragraph.text for paragraph in document.paragraphs])
    return text

def extract_text_from_txt(file_content):
    text = file_content.decode('utf-8')  # Convert bytes to string
    return text

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_to_db(file, filename, user_id, task_id):
    timestamp = datetime.datetime.utcnow().isoformat()
    file_id = fs.put(file, filename=filename)
    db.insert_one("DownloadedFiles", {"filename": filename, "file_id": file_id, "user_id": user_id, "task_id": task_id, "timestamp": timestamp})
    return file_id

def get_file_from_db(file_id):
    file = fs.get(ObjectId(file_id))
    return file

@file_routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    task_id = request.form.get('task_id')
    text = ''
    timestamp = datetime.datetime.utcnow().isoformat()

    if not task_id:
        return {"error": "No task_id provided"}, 400
    if 'file' not in request.files:
        return {"error": "No file part"}, 400
    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_content = file.read()
        file_id = save_file_to_db(file_content, filename, user_id, task_id)

        if filename.rsplit('.', 1)[1].lower() == 'pdf':
            text = extract_text_from_pdf(file_content)
        elif filename.rsplit('.', 1)[1].lower() == 'docx':
            text = extract_text_from_docx(file_content)
        elif filename.rsplit('.', 1)[1].lower() == 'txt':
            text = extract_text_from_txt(file_content)

        db.insert_one("FileData", {"text": text, "user_id": user_id, "task_id": task_id, "timestamp": timestamp})
        train_model(task_id)
        return {"message": "File uploaded, text extracted and model trained successfully"}, 200
    else:
        return {"error": "File type not allowed"}, 400
