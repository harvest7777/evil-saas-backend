import requests
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

url = "http://localhost:5000/"
def test_api():
    TEST_TOKEN = os.getenv("TEST_TOKEN")
    full_url = url + "secure-endpoint"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}"
    }
    response = requests.get(full_url, headers=headers)
    print(response.json())

def test_supabase():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    response = (
        supabase.table("test")
        .insert({ "chunk_content": "Pluto"})
        .execute()
    )
    print(response)
if __name__ == "__main__":
    test_supabase()