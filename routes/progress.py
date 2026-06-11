from flask import Blueprint, render_template, session, jsonify
import datetime
import collections
from routes import get_supabase, login_required, calculate_streak

bp = Blueprint('progress', __name__, url_prefix='/progress')
supabase = get_supabase()

@bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    
    logs_res = supabase.table('workout_logs').select('date').eq('user_id', user_id).execute()
    total_workouts = len(logs_res.data) if logs_res.data else 0
    completed_dates = {log['date'] for log in logs_res.data} if logs_res.data else set()
    
    streak = calculate_streak(user_id, supabase) 
    
    # Výpočet zmeškaných tréningov od registrácie a od vytvorenia tréningového splitu
    today = datetime.date.today()
    user_res = supabase.table('users').select('created_at').eq('id', user_id).execute()
    user_registered_date = today
    if user_res.data:
        try:
            user_registered_date = datetime.date.fromisoformat(user_res.data[0]['created_at'][:10])
        except Exception:
            pass
            
    all_progs = supabase.table('programs').select('id, created_at, is_active').eq('user_id', user_id).order('created_at').execute()
    
    missed_since_registration = 0
    missed_since_active_split = 0
    
    if all_progs.data:
        prog_ids = [p['id'] for p in all_progs.data]
        wd_res = supabase.table('workout_days').select('program_id, day_of_week').in_('program_id', prog_ids).execute()
        
        scheduled_dows_by_prog = collections.defaultdict(set)
        for wd in wd_res.data:
            scheduled_dows_by_prog[wd['program_id']].add(wd['day_of_week'])
            
        for index, prog in enumerate(all_progs.data):
            prog_id = prog['id']
            prog_created = datetime.date.fromisoformat(prog['created_at'][:10])
            
            if index + 1 < len(all_progs.data):
                next_prog_created = datetime.date.fromisoformat(all_progs.data[index+1]['created_at'][:10])
                prog_end = next_prog_created - datetime.timedelta(days=1)
            else:
                prog_end = today - datetime.timedelta(days=1)
                
            prog_sched = scheduled_dows_by_prog[prog_id]
            if prog_sched:
                curr = prog_created
                while curr <= prog_end:
                    curr_str = curr.isoformat()
                    if curr.weekday() in prog_sched:
                        if curr_str not in completed_dates:
                            missed_since_registration += 1
                            if prog.get('is_active'):
                                missed_since_active_split += 1
                    curr += datetime.timedelta(days=1)
    
    set_logs_res = supabase.table('set_logs').select('exercise_name, workout_logs!inner(user_id)').eq('workout_logs.user_id', user_id).execute() 
    unique_exercises = []
    if set_logs_res.data:
        unique_exercises = sorted(list(set(item['exercise_name'] for item in set_logs_res.data)))
        
    return render_template('progress.html', 
                           total_workouts=total_workouts, 
                           missed_since_registration=missed_since_registration,
                           missed_since_active_split=missed_since_active_split,
                           streak=streak,
                           unique_exercises=unique_exercises)

@bp.route('/api/consistency')
@login_required
def api_consistency():
    user_id = session['user_id']
    
    # 1. Načítanie aktívneho programu, jeho dňa vytvorenia a naplánovaných dní
    prog_res = supabase.table('programs').select('id, created_at').eq('user_id', user_id).eq('is_active', True).execute()
    if not prog_res.data:
        return jsonify({'labels': [], 'data': [], 'statuses': [], 'types': [], 'colors': []})
        
    program_id = prog_res.data[0]['id']
    program_created_date = datetime.date.fromisoformat(prog_res.data[0]['created_at'][:10])
    
    wd_res = supabase.table('workout_days').select('id, day_of_week, day_type').eq('program_id', program_id).execute()
    scheduled_dows = {wd['day_of_week'] for wd in wd_res.data} if wd_res.data else set()
    wd_by_dow = {wd['day_of_week']: wd for wd in wd_res.data} if wd_res.data else {}
    
    # 2. Načítanie všetkých odcvičených tréningov
    logs_res = supabase.table('workout_logs').select('date, started_at, finished_at, workout_day_id').eq('user_id', user_id).execute()
    
    # Zmapovanie logov podľa dátumu
    logs_by_date = {}
    if logs_res.data:
        for log in logs_res.data:
            dt_date = log.get('date')
            if dt_date:
                logs_by_date[dt_date] = log

    # 3. Generovanie časovej osi končiacej dnešným dňom
    today = datetime.date.today()
    
    from flask import request
    range_val = request.args.get('range', 'month')
    if range_val == 'week':
        timeline_days = 7
    elif range_val == 'month':
        timeline_days = 30
    elif range_val == '6months':
        timeline_days = 180
    elif range_val == 'year':
        timeline_days = 365
    elif range_val == 'all':
        timeline_days = max(1, (today - program_created_date).days + 1)
    else:
        timeline_days = 30
    
    labels = []
    durations = []
    statuses = [] # 'completed', 'missed', 'rest', 'today_planned'
    day_types = []
    colors = []
    
    slovak_days = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]
    
    # Farebná paleta pre jednotlivé splity / stavy tréningov
    color_map = {
        'Upper': '#3a86ff',        # Žiarivá modrá
        'Lower': '#ff006e',        # Žiarivá ružová
        'Full Body': '#8338ec',    # Fialová
        'Push': '#fb5607',         # Jasná oranžová
        'Pull': '#023e8a',         # Tmavomodrá indigo
        'Legs': '#38b000',         # Zelená
    }
    
    for i in range(timeline_days - 1, -1, -1):
        check_date = today - datetime.timedelta(days=i)
        check_date_str = check_date.isoformat()
        dow = check_date.weekday()
        
        # Nezobrazovať dni pred vytvorením aktívneho programu
        if check_date < program_created_date:
            continue
            
        day_name = slovak_days[dow]
        label = f"{day_name} {check_date.day}.{check_date.month}."
        labels.append(label)
        
        # A. Tréning odcvičený
        if check_date_str in logs_by_date:
            log = logs_by_date[check_date_str]
            duration_minutes = 0
            start = log.get('started_at')
            finish = log.get('finished_at')
            if start and finish:
                try:
                    import dateutil.parser
                    start_dt = dateutil.parser.isoparse(start)
                    finish_dt = dateutil.parser.isoparse(finish)
                    duration_minutes = (finish_dt - start_dt).total_seconds() / 60.0
                except Exception:
                    pass
            # Ak je trvanie 0 alebo chýba, dáme default 45 min
            if duration_minutes <= 0:
                duration_minutes = 45.0
                
            durations.append(round(duration_minutes, 1))
            statuses.append('completed')
            
            # Zistenie typu tréningu, ktorý bol odcvičený
            logged_wd_id = log.get('workout_day_id')
            dtype = 'Cvičenie'
            for wd in wd_res.data:
                if wd['id'] == logged_wd_id:
                    dtype = wd['day_type']
                    break
            day_types.append(dtype)
            
            # Nastavenie farby podľa typu tréningu
            colors.append(color_map.get(dtype, '#0dcaf0'))
            
        # B. Tréning neodcvičený
        else:
            # Bol na tento deň naplánovaný tréning?
            if dow in scheduled_dows:
                # Ak je to dnes, tréning je zatiaľ iba naplánovaný (nie zmeškaný)
                if check_date == today:
                    labels[-1] = labels[-1] + " (Dnes)"
                    durations.append(15.0) # Ukážeme menší žltý stĺpec
                    statuses.append('today_planned')
                    dtype = wd_by_dow[dow]['day_type']
                    day_types.append(f"Dnes: {dtype}")
                    colors.append('#ffc107') # Žltá pre dnešný naplánovaný tréning
                else:
                    # Zmeškaný tréning v minulosti
                    durations.append(0.0) # 0 minút pre zmeškaný
                    statuses.append('missed')
                    dtype = wd_by_dow[dow]['day_type']
                    day_types.append(f"Zmeškaný ({dtype})")
                    colors.append('#c53030') # Červená pre zmeškaný tréning
            else:
                # Voľný deň (Rest day)
                durations.append(0.0) # 0 minút pre voľno
                statuses.append('rest')
                day_types.append('Voľno')
                colors.append('#495057') # Tmavosivá pre rest day
                
    return jsonify({
        'labels': labels,
        'data': durations,
        'statuses': statuses,
        'types': day_types,
        'colors': colors
    })

@bp.route('/api/exercise/<name>')
@login_required
def api_exercise(name):
    user_id = session['user_id']
    set_res = supabase.table('set_logs').select('weight_kg, reps, workout_logs!inner(date, user_id)').eq('workout_logs.user_id', user_id).eq('exercise_name', name).eq('is_warmup', False).execute()
    
    date_max_weight = collections.defaultdict(float)
    date_max_reps = collections.defaultdict(int)
    
    if set_res.data:
        for s in set_res.data:
            if not s.get('workout_logs'):
                continue
            date_str = s['workout_logs']['date']
            w = s['weight_kg'] or 0
            r = s['reps'] or 0
            
            if w > date_max_weight[date_str]:
                date_max_weight[date_str] = w
            if r > date_max_reps[date_str]:
                date_max_reps[date_str] = r
                
    dates = sorted(date_max_weight.keys())
    return jsonify({
        'labels': dates,
        'max_weight': [date_max_weight[d] for d in dates],
        'max_reps': [date_max_reps[d] for d in dates]
    })
