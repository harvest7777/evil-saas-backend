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
supabase: Client = create_client(url, key)

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

def get_file_metadata(file_uuid: str) -> dict | None:
    res = supabase.table("file_metadata").select("*").eq("file_uuid", file_uuid).single().execute()
    print("\n\nSUCCESSFULLY FETCHED FROM SUPABASE\n\n")
    return res.data

def get_file(file_name: str, owner_uuid: str) -> bytes | None:
    bucket_name = "user-files"
    file_path = f"{owner_uuid}/{file_name}"
    file_bytes = supabase.storage.from_(bucket_name).download(file_path)
    return file_bytes

def embed_file(file_uuid: str,text: str):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # or your preferred embedding model
    )
    res = supabase.table("file_content_embeddings").insert({
        "embedding": response.data[0].embedding,
        "file_uuid": file_uuid,
        "chunk_content": text
    }).execute()

def split_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))

    return chunks

def sanitize(text):
    return text.replace("\x00", "")

def query(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    embedded_query = response.data[0].embedding
    res = supabase.rpc("match_documents", {
        "query_embedding": embedded_query,
        "match_threshold": 0.2,
        "match_count": 5
    }).execute()
    print(len(res.data))
    

if __name__ == "__main__":
    embed_file("hi")
