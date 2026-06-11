import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Try fetching logs without user_id first to see if any exist
print("Fetching all set_logs...")
all_logs = supabase.table('set_logs').select('*, workout_logs(*)').limit(5).execute()
print("All logs sample:", all_logs.data)

print("\nFetching with inner join...")
try:
    # Get a valid user id from workout logs
    user_res = supabase.table('workout_logs').select('user_id').limit(1).execute()
    if user_res.data:
        user_id = user_res.data[0]['user_id']
        print(f"Testing with user_id: {user_id}")
        joined = supabase.table('set_logs').select('exercise_name, workout_logs!inner(user_id)').eq('workout_logs.user_id', user_id).execute()
        print("Joined logs sample:", joined.data[:5] if joined.data else "No data")
    else:
        print("No workout logs found to test with.")
except Exception as e:
    print("Error:", e)
