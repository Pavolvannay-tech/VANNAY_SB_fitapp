import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")

# Create client with service_role key to bypass rate limits
supabase: Client = create_client(url, key)

try:
    # Use admin api to create a user, bypasses email rate limit and auto confirms
    user = supabase.auth.admin.create_user({
        "email": "test@test.sk",
        "password": "password123",
        "email_confirm": True
    })
    print(f"Successfully created test user: {user.user.id}")
    
    # insert into public.users just in case
    try:
        supabase.table("users").insert({
            "id": user.user.id,
            "email": "test@test.sk",
            "onboarding_done": False
        }).execute()
        print("User inserted into public.users table.")
    except Exception as e:
        print(f"Error inserting to public.users: {e}")
        
except Exception as e:
    print(f"Error creating user: {e}")
