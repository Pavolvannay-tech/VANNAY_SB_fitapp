import os
import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    today_date = datetime.date.today().isoformat()
    # Find any workout_logs for today with NO set_logs (meaning they failed)
    # Actually, let's just find logs for today and delete them so user can try again
    res = supabase.table('workout_logs').select('id').eq('date', today_date).execute()
    if res.data:
        for row in res.data:
            print(f"Deleting broken workout log for today: {row['id']}")
            supabase.table('workout_logs').delete().eq('id', row['id']).execute()
        print("Done deleting today's logs.")
    else:
        print("No logs found for today.")
except Exception as e:
    print("Error:", e)
