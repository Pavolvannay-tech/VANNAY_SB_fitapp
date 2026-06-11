import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

response = supabase.table("users").select("*").execute()
print("USERS IN DB:")
for u in response.data:
    print(f"ID: {u['id']}, Email: {u.get('email', 'N/A')}")
