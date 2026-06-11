import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from routes import get_supabase, login_required

bp = Blueprint('workout', __name__, url_prefix='/workout')
supabase = get_supabase()

@bp.route('/')
@login_required
def start():
    user_id = session['user_id']
    
    prog_res = supabase.table('programs').select('id, split_type').eq('user_id', user_id).eq('is_active', True).execute()
    if not prog_res.data:
        flash("Nenašli sme aktívny program. Prosím vygeneruj si nový na Dashboarde.", "warning")
        return redirect(url_for('dashboard.index'))
        
    program = prog_res.data[0]
    
    # Get all workout days for this program
    wd_res = supabase.table('workout_days').select('*').eq('program_id', program['id']).order('day_of_week').execute()
    workout_days = wd_res.data
    
    # Get completed workout logs for the calendar
    logs_res = supabase.table('workout_logs').select('date, workout_day_id, total_volume_kg').eq('user_id', user_id).execute()
    workout_logs = logs_res.data if logs_res.data else []
    
    # Pre-map workout days for ease of use in mapping logs on the frontend
    wd_map = {wd['id']: wd for wd in workout_days}
    for log in workout_logs:
        wd_id = log['workout_day_id']
        if wd_id in wd_map:
            log['day_type'] = wd_map[wd_id]['day_type']
            log['day_of_week'] = wd_map[wd_id]['day_of_week']
        else:
            log['day_type'] = 'Cvičenie'
            log['day_of_week'] = -1
            
    today_dow = datetime.datetime.now().weekday()
    # Find if there is a workout scheduled for today
    today_workout = next((wd for wd in workout_days if wd['day_of_week'] == today_dow), None)
            
    return render_template('workout_launcher.html', 
                           program=program, 
                           workout_days=workout_days, 
                           workout_logs=workout_logs,
                           today_workout=today_workout)

@bp.route('/cvicit')
@login_required
def cvicit():
    user_id = session['user_id']
    
    prog_res = supabase.table('programs').select('id, split_type').eq('user_id', user_id).eq('is_active', True).execute()
    if not prog_res.data:
        flash("Nenašli sme aktívny program. Prosím vygeneruj si nový na Dashboarde.", "warning")
        return redirect(url_for('dashboard.index'))
        
    program = prog_res.data[0]
    
    # Get all workout days for this program
    wd_res = supabase.table('workout_days').select('*').eq('program_id', program['id']).order('day_of_week').execute()
    workout_days = wd_res.data
    
    today_dow = datetime.datetime.now().weekday()
    # Find if there is a workout scheduled for today
    today_workout = next((wd for wd in workout_days if wd['day_of_week'] == today_dow), None)
    
    return render_template('workout_cvicit.html',
                           program=program,
                           workout_days=workout_days,
                           today_workout=today_workout)

@bp.route('/session/<workout_day_id>')
@login_required
def session_workout(workout_day_id):
    user_id = session['user_id']
    date_val = request.args.get('date', datetime.date.today().isoformat())
    
    # Check if there is already an active workout of a different type
    active_id = session.get('active_workout_day_id')
    if active_id and active_id != workout_day_id:
        flash(f"Už máš rozrobený tréning: {session.get('active_workout_name')}. Najskôr ho dokonči alebo zruš.", "warning")
        return redirect(url_for('workout.cvicit'))
        
    # Blokovať spätné zapisovanie tréningov
    if date_val != datetime.date.today().isoformat():
        flash("Spätné zapisovanie tréningov je zakázané. Sústreď sa na dnešný tréning!", "warning")
        return redirect(url_for('workout.start'))
        
    # Fetch the workout day
    wd_res = supabase.table('workout_days').select('*').eq('id', workout_day_id).execute()
    if not wd_res.data:
        flash("Tréningový deň nebol nájdený.", "danger")
        return redirect(url_for('workout.start'))
        
    workout_day = wd_res.data[0]
    
    # Store active workout in session
    session['active_workout_day_id'] = workout_day_id
    session['active_workout_name'] = workout_day['day_type']
    
    # Fetch exercises for this day
    ex_res = supabase.table('program_exercises').select('*').eq('workout_day_id', workout_day_id).order('order_index').execute()
    exercises = ex_res.data
    
    # Fetch previous weight logs for progressive overload target
    for ex in exercises:
        try:
            last_log = supabase.table('set_logs').select('*, workout_logs!inner(user_id)').eq('workout_logs.user_id', user_id).eq('exercise_name', ex['name']).eq('is_warmup', False).order('created_at', desc=True).limit(1).execute()
            if last_log.data:
                ex['last_weight'] = last_log.data[0]['weight_kg']
                ex['last_reps'] = last_log.data[0]['reps']
                
                if ex['is_compound'] and ex['last_weight']:
                    ex['wu1_w'] = round(ex['last_weight'] * 0.6)
                    ex['wu1_r'] = 5
                    ex['wu2_w'] = round(ex['last_weight'] * 0.85)
                    ex['wu2_r'] = 2
            else:
                ex['last_weight'] = None
        except Exception:
            ex['last_weight'] = None
            
    is_retro = date_val != datetime.date.today().isoformat()
    return render_template('workout.html', workout=workout_day, exercises=exercises, date=date_val, is_retro=is_retro)

@bp.route('/active')
@login_required
def active_workout():
    active_id = session.get('active_workout_day_id')
    if not active_id:
        flash("Nemáš žiadny rozrobený tréning.", "info")
        return redirect(url_for('workout.cvicit'))
    return redirect(url_for('workout.session_workout', workout_day_id=active_id))

@bp.route('/cancel')
@login_required
def cancel_workout():
    session.pop('active_workout_day_id', None)
    session.pop('active_workout_name', None)
    flash("Tréning bol zrušený.", "info")
    return redirect(url_for('workout.start'))

@bp.route('/save', methods=['POST'])
@login_required
def save_log():
    user_id = session['user_id']
    data = request.json
    
    if not data or 'workout_day_id' not in data:
        return {"error": "Zlé dáta, chýba identifikátor trénerového dňa."}, 400
        
    target_date = data.get('date', datetime.date.today().isoformat())
    
    # Check if a log already exists for this user on this specific target_date
    existing = supabase.table('workout_logs').select('id').eq('user_id', user_id).eq('date', target_date).execute()
    if existing.data:
        # Prepísanie (overwrite) - zmažeme staré sety a log pre tento deň
        existing_log_id = existing.data[0]['id']
        try:
            supabase.table('set_logs').delete().eq('workout_log_id', existing_log_id).execute()
        except Exception:
            pass
        try:
            supabase.table('workout_logs').delete().eq('id', existing_log_id).execute()
        except Exception:
            pass
        
    duration_seconds = data.get('duration_seconds', 0)
    finished_at_dt = datetime.datetime.now()
    started_at_dt = finished_at_dt - datetime.timedelta(seconds=int(duration_seconds))
    
    log_res = supabase.table('workout_logs').insert({
        'user_id': user_id,
        'workout_day_id': data['workout_day_id'],
        'date': target_date,
        'started_at': started_at_dt.isoformat(),
        'finished_at': finished_at_dt.isoformat(),
        'completed': True
    }).execute()
    workout_log_id = log_res.data[0]['id']
    total_volume = 0
    sets_data = data.get('sets', [])
    sets_to_insert = []
    
    for s in sets_data:
        weight = float(s['weight'])
        reps = int(s['reps'])
        total_volume += (weight * reps)
        sets_to_insert.append({
            'workout_log_id': workout_log_id,
            'exercise_id': s['exercise_id'],
            'exercise_name': s['exercise_name'],
            'set_number': int(s['set_number']),
            'weight_kg': weight,
            'reps': reps,
            'is_warmup': False,
            'reached_failure': s.get('failure', False)
        })
        
    import collections
    
    # Načítanie naplánovaných sérií cvikov pre tento deň
    exercises_res = supabase.table('program_exercises').select('name, sets_working').eq('workout_day_id', data['workout_day_id']).execute()
    scheduled_sets_by_ex = {ex['name']: ex['sets_working'] for ex in exercises_res.data} if exercises_res.data else {}
    
    progresnute_serie = 0
    rovnake_serie = 0
    neprogresnute_serie = 0
    skipnute_serie = 0
    
    # Zoskupenie dnes odcvičených sérií podľa názvu cviku
    today_sets_by_ex = collections.defaultdict(list)
    for s in sets_data:
        today_sets_by_ex[s['exercise_name']].append(s)
        
    for ex_name, sched_sets in scheduled_sets_by_ex.items():
        prev_sets_map = {}
        try:
            # Načítanie všetkých historických sérií pre daného používateľa a cvik
            prev_logs = supabase.table('set_logs').select('weight_kg, reps, set_number, workout_logs!inner(date)').eq('workout_logs.user_id', user_id).eq('exercise_name', ex_name).execute()
            if prev_logs.data:
                # Nájdeme najnovší predošlý tréning (ktorý nie je dnes)
                dates = {l['workout_logs']['date'] for l in prev_logs.data if l['workout_logs']['date'] != target_date}
                if dates:
                    latest_prev_date = max(dates)
                    for l in prev_logs.data:
                        if l['workout_logs']['date'] == latest_prev_date:
                            set_num = int(l['set_number'])
                            prev_sets_map[set_num] = (float(l['weight_kg'] or 0), int(l['reps'] or 0))
        except Exception as e:
            print("Chyba pri načítaní predošlých sérií:", e)
            
        # Zmapovanie dnešných sérií
        today_completed = today_sets_by_ex.get(ex_name, [])
        today_sets_map = {int(s['set_number']): (float(s['weight']), int(s['reps'])) for s in today_completed}
        
        # Porovnanie naplánovaných sérií
        for set_num in range(1, sched_sets + 1):
            if set_num not in today_sets_map:
                skipnute_serie += 1
            else:
                today_w, today_r = today_sets_map[set_num]
                if set_num not in prev_sets_map:
                    # Prvýkrát cvičená séria alebo chýba predošlá -> Progres
                    progresnute_serie += 1
                else:
                    prev_w, prev_r = prev_sets_map[set_num]
                    if (today_w > prev_w) or (today_w == prev_w and today_r > prev_r):
                        progresnute_serie += 1
                    elif today_w == prev_w and today_r == prev_r:
                        rovnake_serie += 1
                    else:
                        neprogresnute_serie += 1
                        
        # Porovnanie prípadných extra odcvičených sérií nad plán
        for set_num, (today_w, today_r) in today_sets_map.items():
            if set_num > sched_sets:
                if set_num not in prev_sets_map:
                    progresnute_serie += 1
                else:
                    prev_w, prev_r = prev_sets_map[set_num]
                    if (today_w > prev_w) or (today_w == prev_w and today_r > prev_r):
                        progresnute_serie += 1
                    elif today_w == prev_w and today_r == prev_r:
                        rovnake_serie += 1
                    else:
                        neprogresnute_serie += 1
                        
    # Vypocet progresu (jednoduchý odhad podľa max váhy v porovnaní s predošlým tréningom)
    progress_count = 0
    unique_exercises = {s['exercise_name'] for s in sets_data}
    total_exercises = len(unique_exercises)
    
    for ex_name in unique_exercises:
        try:
            last_log_res = supabase.table('set_logs').select('weight_kg, workout_logs!inner(user_id)').eq('workout_logs.user_id', user_id).eq('exercise_name', ex_name).eq('is_warmup', False).order('created_at', desc=True).limit(1).execute()
            today_max_weight = max([float(s['weight']) for s in sets_data if s['exercise_name'] == ex_name])
            
            if last_log_res.data:
                last_weight = last_log_res.data[0]['weight_kg'] or 0
                if today_max_weight > last_weight:
                    progress_count += 1
            else:
                progress_count += 1 # Prvýkrát je tiež progres
        except Exception:
            pass

    if sets_to_insert:
        supabase.table('set_logs').insert(sets_to_insert).execute()
        
    supabase.table('workout_logs').update({'total_volume_kg': total_volume}).eq('id', workout_log_id).execute()
    
    # Zistime streak (počet odtrénovaných dní celkovo)
    logs_res = supabase.table('workout_logs').select('id').eq('user_id', user_id).execute()
    streak = len(logs_res.data) if logs_res.data else 1
    
    # Clear the active workout from session
    session.pop('active_workout_day_id', None)
    session.pop('active_workout_name', None)
    
    return {
        "redirect": url_for('workout.summary', 
                            duration=duration_seconds, 
                            streak=streak, 
                            progress_count=progress_count, 
                            total_exercises=total_exercises,
                            progresnute=progresnute_serie,
                            rovnake=rovnake_serie,
                            neprogresnute=neprogresnute_serie,
                            skipnute=skipnute_serie)
    }

@bp.route('/summary')
@login_required
def summary():
    duration = int(request.args.get('duration', 0))
    streak = request.args.get('streak', 0)
    progress_count = request.args.get('progress_count', 0)
    total_exercises = request.args.get('total_exercises', 0)
    
    progresnute = request.args.get('progresnute', 0)
    rovnake = request.args.get('rovnake', 0)
    neprogresnute = request.args.get('neprogresnute', 0)
    skipnute = request.args.get('skipnute', 0)
    
    m, s = divmod(duration, 60)
    duration_str = f"{m:02d}:{s:02d}"
    
    return render_template('workout_summary.html', 
                           duration_str=duration_str, 
                           streak=streak, 
                           progress_count=progress_count, 
                           total_exercises=total_exercises,
                           progresnute=progresnute,
                           rovnake=rovnake,
                           neprogresnute=neprogresnute,
                           skipnute=skipnute)
