import json
import jwt
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
client = OpenAI()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

def get_user_supabase_client(access_token):
    client = create_client(url, key)
    client.auth.set_session(access_token, access_token)
    return client

def verify_token(token) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        return payload  
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None

def get_file_metadata(file_uuid: str, supabase: Client) -> dict | None:
    res = supabase.table("file_metadata").select("*").eq("file_uuid", file_uuid).single().execute()
    print("\n\nSUCCESSFULLY FETCHED FROM SUPABASE\n\n")
    return res.data

def get_file(file_name: str, owner_uuid: str, supabase: Client) -> bytes | None:
    bucket_name = "user-files"
    file_path = f"{owner_uuid}/{file_name}"
    file_bytes = supabase.storage.from_(bucket_name).download(file_path)
    return file_bytes

def embed_file(file_uuid: str,text: str, supabase: Client):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  
    )
    res = supabase.table("file_content_embeddings").insert({
        "embedding": response.data[0].embedding,
        "file_uuid": file_uuid,
        "chunk_content": text
    }).execute()

def embed_query (text: str):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def query_vectors(embedded_query, supabase: Client, match_threshold=0.0, match_count=5):
    response = (
        supabase.rpc("match_documents", {
            "query_embedding": embedded_query,
            "match_threshold": match_threshold,
            "match_count": match_count
        })
        .execute()
    )
    return response.data

def split_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))

    return chunks

def sanitize(text):
    return text.replace("\x00", "")

def query(text, supabase: Client):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    embedded_query = response.data[0].embedding
    res = supabase.rpc("match_documents", {
        "query_embedding": embedded_query,
        "match_threshold": 0.7,
        "match_count": 5
    }).execute()
    print(len(res.data))
    

def download_file(folder: str, file_name: str, supabase: Client) -> bytes | None:
    response = (
        supabase.storage
        .from_("user-files")
        .download(f"{folder}/{file_name}")
    )
    return response

def insert_response(chat_id: int, response: str, supabase: Client) -> str:
    res = supabase.table("messages").insert({
        "chat_id": chat_id,
        "role":"assistant",
        "message_content": response
    }).execute()
    return res.data

def generate_response(context: str, user_prompt: str ):
    system_prompt = f"""You are a helpful AI assistant. Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

User question:
{user_prompt}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], 
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


if __name__ == "__main__":
    embed_file("hi")
