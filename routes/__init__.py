import os
from supabase import create_client, Client
from functools import wraps
from flask import session, redirect, url_for

# Tento inicializačný súbor vráti Supabase klienta pre aktuálne prostredie použitého vo view routách
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

# Helper dekorátor pre routes, kde treba byť prihlásený
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Kontrola, či používateľ má dokončený onboarding
        if session.get('onboarding_done') is False and f.__name__ not in ('step1', 'step2', 'step3', 'step4', 'step5'):
            return redirect(url_for('onboarding.step1'))
            
        return f(*args, **kwargs)
    return decorated_function

def calculate_streak(user_id, supabase) -> int:
    import datetime
    
    prog_res = supabase.table('programs').select('id, created_at').eq('user_id', user_id).eq('is_active', True).execute()
    if not prog_res.data:
        return 0
    program_id = prog_res.data[0]['id']
    active_date = datetime.date.fromisoformat(prog_res.data[0]['created_at'][:10])
    
    logs_res = supabase.table('workout_logs').select('date').eq('user_id', user_id).execute()
    completed_dates = {log['date'] for log in logs_res.data} if logs_res.data else set()
    
    wd_res = supabase.table('workout_days').select('day_of_week').eq('program_id', program_id).execute()
    scheduled_dows = {wd['day_of_week'] for wd in wd_res.data} if wd_res.data else set()
    
    if not scheduled_dows:
        return 0
        
    streak = 0
    curr_date = datetime.date.today()
    
    for i in range(365):
        date_check = curr_date - datetime.timedelta(days=i)
        
        # Streak sa nepokazí za dni pred vytvorením tohto programu
        if date_check < active_date:
            break
            
        date_str = date_check.isoformat()
        dow = date_check.weekday()
        
        if dow in scheduled_dows:
            if date_str in completed_dates:
                streak += 1
            else:
                if i == 0:
                    continue
                else:
                    break
    return streak
