from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response, stream_with_context
import json
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
    """
    By knowing the file uuid, I implictly know who owns it and can retrieve file contents.
    """
    data = request.get_json()

    bearer_token = request.headers.get("Authorization").split(" ")[1]
    client = get_user_supabase_client(bearer_token)
    print(json.dumps(data, indent=2))

    # we need to extract some metadata the supabase storage api needs to download the file
    folder = data.get("record").get("uuid")
    file_name = data.get("record").get("file_name")

    # we used to use mimetype becasue we were getting from storage.
    # mimetype = data.get("record").get("metadata").get("mimetype")

    file_bytes = download_file(folder, file_name, client)

    # the mimetype doesnt map to a correct pymupdf type
    # DEPRECATED
    # mimetype_to_pymupdf_type = {
    #     "application/pdf": "pdf",
    #     "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
    # }

    pdf_doc = pymupdf.open(stream=file_bytes, filetype="pdf")

    full_text = ""
    for page_num in range(len(pdf_doc)):
        page = pdf_doc.load_page(page_num)
        full_text += page.get_text()
    
    full_text = sanitize(full_text)
    """
    At this point we have the full text of the document. We can start splitting and embedding. Most edits 
    and tweaks should be done here to test embedding and chunking strategies.
    """

    chunks = split_text(full_text) 
    file_uuid = data.get("record").get("file_uuid")
    for chunk in chunks:
        embed_file(file_uuid, chunk, client)
    return jsonify({"message": "Embed endpoint called successfully"})
    
@app.route("/ask", methods=["POST"])
def ask():
    """
    Take in a query and embed it, then perform a search against vectors. Return the K most similar results.
    """
    data = request.get_json()
    bearer_token = request.headers.get("Authorization").split(" ")[1]
    client = get_user_supabase_client(bearer_token)
    user_question = data.get("message")
    chat_id = data.get("chat_id")

    print("User question:", user_question)

    embedded_question = embed_query(user_question)
    print("Embedded question:", embedded_question[:10])
    matches = query_vectors(embedded_question, client)
    # if len(matches) == 0:
    #     response = "I'm sowwy >.<, I couldn't find any relevant information."
    #     insert_response(chat_id, response, client)
    #     yield response
    # else:
    #     # Modify `generate_response` to yield chunks instead of returning whole string
    #     for chunk in generate_response(matches[0], user_question, client):
    #         yield chunk
    #     insert_response(chat_id, "[STREAMED] Full response handled separately", client)

    return Response(generate_response(matches[0], user_question), content_type="text/plain")

    # return jsonify({"message": "Ask endpoint called successfully", "response": response, "matches": matches})

@app.route("/test", methods=["POST","GET"])
def test():
    data = request.get_json()
    bearer_token = request.headers.get("Authorization").split(" ")[1]

    print(bearer_token)
    return jsonify({"message": "Test endpoint called successfully", "data": data, "token": bearer_token})
if __name__ == "__main__":
    app.run(debug=True)