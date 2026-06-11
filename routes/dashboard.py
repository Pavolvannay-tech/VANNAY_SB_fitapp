import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash
from routes import get_supabase, login_required, calculate_streak
from program_generator import generate_program

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
supabase = get_supabase()

@bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    today_dow = datetime.datetime.now().weekday()
    
    prog_res = supabase.table('programs').select('id').eq('user_id', user_id).eq('is_active', True).execute()
    
    today_workout = None
    exercises = []
    if prog_res.data:
        program_id = prog_res.data[0]['id']
        wd_res = supabase.table('workout_days').select('*').eq('program_id', program_id).eq('day_of_week', today_dow).execute()
        
        if wd_res.data:
            today_workout = wd_res.data[0]
            ex_res = supabase.table('program_exercises').select('*').eq('workout_day_id', today_workout['id']).order('order_index').execute()
            exercises = ex_res.data
            
    logs_res = supabase.table('workout_logs').select('date').eq('user_id', user_id).execute()
    total_workouts = len(logs_res.data) if logs_res.data else 0
    
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    
    week_workouts = 0
    if logs_res.data:
        for log in logs_res.data:
            log_date = datetime.datetime.strptime(log['date'], '%Y-%m-%d').date()
            if log_date >= monday:
                week_workouts += 1
                
    return render_template('dashboard.html', 
                          today_dow=today_dow,
                          today_workout=today_workout,
                          exercises=exercises,
                          total_workouts=total_workouts,
                          week_workouts=week_workouts,
                          streak=calculate_streak(user_id, supabase))

@bp.route('/generate-program', methods=['POST'])
@login_required
def regenerate_program():
    import random
    user_id = session['user_id']
    
    # Pools of exercises from onboarding step 3
    random_options = {
        'exercise_chest_flat': ['Flat Bench Press', 'Pec Deck', 'Cable Chest Flyes'],
        'exercise_chest_incline': ['Incline Barbell Press', 'Incline DB Press', 'Smith Machine Incline'],
        'exercise_back_vertical': ['Pull-ups / Chin-ups', 'Lat Pulldown', 'Cable Pulldown'],
        'exercise_back_horizontal_wide': ['Barbell Row', 'DB Row', 'Cable Row (Wide)'],
        'exercise_back_horizontal_close': ['Close Grip Cable Row', 'Machine Row', 'T-Bar Row'],
        'exercise_shoulders': ['Overhead Barbell Press', 'DB Shoulder Press', 'Machine Shoulder Press'],
        'exercise_triceps': ['Triceps Pulldown', 'Skull Crushers', 'Dips'],
        'exercise_biceps': ['Barbell Curl', 'Preacher Curl', 'Incline DB Curl'],
        'exercise_quads': ['Squat', 'Hack Squat', 'Leg Press'],
        'exercise_hamstrings': ['Romanian Deadlift', 'Leg Curl Machine', 'DB RDL']
    }
    
    updates = {}
    for field, opts in random_options.items():
        updates[field] = random.choice(opts)
        
    try:
        supabase.table('users').update(updates).eq('id', user_id).execute()
    except Exception as e:
        print("Error updating user random exercises:", e)
        
    generate_program(user_id, supabase)
    flash("Skvelé! Tvoj nový tréningový program pre tento cyklus bol vygenerovaný.", "success")
    return redirect(url_for('dashboard.index'))
