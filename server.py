from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from auth import *
import pymupdf

app = Flask(__name__)
CORS(app)

load_dotenv()


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the API"})

@app.route("/embed", methods=["POST"])
def embed():
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header else None
    file_uuid = request.json.get("file_uuid")
    print("Received file_uuid:", file_uuid)

    #ill need to deduct credits from user account every time they call some endpoint which calls openai
    token_data = verify_token(token)
    if not token_data:
        return jsonify({"error": "Unauthorized"}), 401
    else:
        uuid = token_data.get("sub")

    file_data = get_file_metadata(file_uuid)
    file_name = file_data.get("file_name")
    file_bytes = get_file(file_name, uuid)
    pdf_doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    full_text = ""
    for page_num in range(len(pdf_doc)):
        page = pdf_doc.load_page(page_num)
        full_text += page.get_text()

    full_text = sanitize(full_text)
    chunks = split_text(full_text) 
    for chunk in chunks:
        embed_file(file_uuid, chunk)
    return jsonify({"file_data":file_data}) 

@app.route("/test", methods=["GET"])
def test_endpoint():
    return jsonify({"message": "This is a test endpoint"})

@app.route("/query", methods=["POST"])
def query_endpoint():
    text = request.json.get("query")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    query(text)
    return jsonify({"message": "Query executed successfully"})