import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from routes import get_supabase, login_required

bp = Blueprint('profile', __name__, url_prefix='/profile')
supabase = get_supabase()

@bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    user_res = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    user = user_res.data[0] if user_res.data else {}
    
    prog_res = supabase.table('programs').select('id, split_type').eq('user_id', user_id).eq('is_active', True).execute()
    program = prog_res.data[0] if prog_res.data else None
    
    workout_days = []
    if program:
        wd_res = supabase.table('workout_days').select('*').eq('program_id', program['id']).order('order_index').execute()
        for wd in wd_res.data:
            ex_res = supabase.table('program_exercises').select('id, name, sets_working, reps_min, reps_max, is_compound, rest_seconds').eq('workout_day_id', wd['id']).order('order_index').execute()
            wd['exercises'] = ex_res.data
            workout_days.append(wd)
            
    today = datetime.date.today().isoformat()
    return render_template('profile.html', user=user, workout_days=workout_days, program=program, today=today)

@bp.route('/update', methods=['POST'])
@login_required
def update():
    user_id = session['user_id']
    data = {
        'name': request.form.get('name'),
        'age': int(request.form.get('age')),
        'weight_kg': float(request.form.get('weight_kg')),
        'height_cm': float(request.form.get('height_cm')),
        'gender': request.form.get('gender') # can be disabled to change in UI but endpoint supports it
    }
    supabase.table('users').update(data).eq('id', user_id).execute()
    session['name'] = data['name']
    flash("Profil bol úspešne upravený.", "success")
    return redirect(url_for('profile.index'))

@bp.route('/log-weight', methods=['POST'])
@login_required
def log_weight():
    user_id = session['user_id']
    date = request.form.get('date')
    weight = float(request.form.get('weight_kg'))
    
    existing = supabase.table('body_logs').select('id').eq('date', date).eq('user_id', user_id).execute()
    if existing.data:
        supabase.table('body_logs').update({'weight_kg': weight}).eq('id', existing.data[0]['id']).execute()
    else:
        supabase.table('body_logs').insert({'user_id': user_id, 'date': date, 'weight_kg': weight}).execute()
        
    supabase.table('users').update({'weight_kg': weight}).eq('id', user_id).execute()
    
    flash("Aktuálna telesná váha bola zaznamenaná.", "success")
    return redirect(url_for('profile.index'))

@bp.route('/api/weight-history')
@login_required
def api_weight_history():
    user_id = session['user_id']
    logs_res = supabase.table('body_logs').select('date, weight_kg').eq('user_id', user_id).order('date').execute()
    
    dates = []
    weights = []
    if logs_res.data:
        for log in logs_res.data:
            dates.append(log['date'])
            weights.append(log['weight_kg'])
            
    return jsonify({
        'labels': dates,
        'weights': weights
    })

@bp.route('/training')
@login_required
def training_settings():
    user_id = session['user_id']
    user_res = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    user = user_res.data[0] if user_res.data else {}
    
    prog_res = supabase.table('programs').select('id, split_type').eq('user_id', user_id).eq('is_active', True).execute()
    program = prog_res.data[0] if prog_res.data else None
    
    workout_days = []
    if program:
        wd_res = supabase.table('workout_days').select('*').eq('program_id', program['id']).order('order_index').execute()
        for wd in wd_res.data:
            ex_res = supabase.table('program_exercises').select('*').eq('workout_day_id', wd['id']).order('order_index').execute()
            wd['exercises'] = ex_res.data
            workout_days.append(wd)
            
    return render_template('profile_training.html', user=user, workout_days=workout_days, program=program)

@bp.route('/training/update', methods=['POST'])
@login_required
def training_update():
    user_id = session['user_id']
    
    prog_res = supabase.table('programs').select('id').eq('user_id', user_id).eq('is_active', True).execute()
    if not prog_res.data:
        flash("Nenašiel sa žiadny aktívny program.", "danger")
        return redirect(url_for('profile.training_settings'))
        
    program_id = prog_res.data[0]['id']
    wd_res = supabase.table('workout_days').select('id').eq('program_id', program_id).execute()
    wd_ids = [wd['id'] for wd in wd_res.data]
    
    if not wd_ids:
        flash("Program nemá žiadne tréningové dni.", "danger")
        return redirect(url_for('profile.training_settings'))
        
    ex_res = supabase.table('program_exercises').select('id').in_('workout_day_id', wd_ids).execute()
    
    updated_count = 0
    for ex in ex_res.data:
        ex_id = ex['id']
        name = request.form.get(f"name_{ex_id}")
        sets = request.form.get(f"sets_{ex_id}")
        reps_min = request.form.get(f"reps_min_{ex_id}")
        reps_max = request.form.get(f"reps_max_{ex_id}")
        rest = request.form.get(f"rest_{ex_id}")
        is_compound = f"is_compound_{ex_id}" in request.form
        
        if name and sets and reps_min and reps_max and rest:
            try:
                data = {
                    'name': name.strip(),
                    'sets_working': int(sets),
                    'reps_min': int(reps_min),
                    'reps_max': int(reps_max),
                    'rest_seconds': int(rest),
                    'is_compound': is_compound
                }
                supabase.table('program_exercises').update(data).eq('id', ex_id).execute()
                updated_count += 1
            except ValueError:
                pass
                
    # Update workout days day_of_week
    for wd in wd_res.data:
        dow = request.form.get(f"day_of_week_{wd['id']}")
        if dow is not None:
            try:
                supabase.table('workout_days').update({'day_of_week': int(dow)}).eq('id', wd['id']).execute()
                updated_count += 1
            except Exception:
                pass

    if updated_count > 0:
        flash("Tréningový plán bol úspešne upravený.", "success")
    else:
        flash("Neboli vykonané žiadne zmeny.", "info")
        
    return redirect(url_for('profile.training_settings'))

@bp.route('/training/update_exercise/<exercise_id>', methods=['POST'])
@login_required
def update_exercise_api(exercise_id):
    data = request.json
    if not data:
        return {"error": "Chýbajúce dáta."}, 400
        
    try:
        update_data = {
            'name': data['name'].strip(),
            'sets_working': int(data['sets']),
            'reps_min': int(data['reps_min']),
            'reps_max': int(data['reps_max']),
            'rest_seconds': int(data['rest']),
            'is_compound': bool(data['is_compound'])
        }
        supabase.table('program_exercises').update(update_data).eq('id', exercise_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('/training/update_day/<day_id>', methods=['POST'])
@login_required
def update_day_api(day_id):
    data = request.json
    if not data or 'day_of_week' not in data:
        return {"error": "Chýbajúce dáta."}, 400
        
    try:
        supabase.table('workout_days').update({'day_of_week': int(data['day_of_week'])}).eq('id', day_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('/training/bulk-timers', methods=['POST'])
@login_required
def training_bulk_timers():
    user_id = session['user_id']
    
    prog_res = supabase.table('programs').select('id').eq('user_id', user_id).eq('is_active', True).execute()
    if not prog_res.data:
        flash("Nenašiel sa žiadny aktívny program.", "danger")
        return redirect(url_for('profile.training_settings'))
        
    program_id = prog_res.data[0]['id']
    wd_res = supabase.table('workout_days').select('id').eq('program_id', program_id).execute()
    wd_ids = [wd['id'] for wd in wd_res.data]
    
    if not wd_ids:
        flash("Program nemá žiadne tréningové dni.", "danger")
        return redirect(url_for('profile.training_settings'))
        
    ex_res = supabase.table('program_exercises').select('id, is_compound').in_('workout_day_id', wd_ids).execute()
    
    bulk_compound = request.form.get('bulk_compound')
    bulk_isolation = request.form.get('bulk_isolation')
    
    updated_count = 0
    for ex in ex_res.data:
        new_val = None
        if bulk_compound and ex['is_compound']:
            try:
                new_val = int(bulk_compound)
            except ValueError:
                pass
        elif bulk_isolation and not ex['is_compound']:
            try:
                new_val = int(bulk_isolation)
            except ValueError:
                pass
                
        if new_val is not None and new_val >= 0:
            supabase.table('program_exercises').update({'rest_seconds': new_val}).eq('id', ex['id']).execute()
            updated_count += 1
            
    if updated_count > 0:
        flash("Časovače medzi sériami boli úspešne hromadne aktualizované.", "success")
    else:
        flash("Neboli vykonané žiadne zmeny v časovačoch.", "info")
        
    return redirect(url_for('profile.training_settings'))

@bp.route('/training/add', methods=['POST'])
@login_required
def training_add():
    workout_day_id = request.form.get('workout_day_id')
    name = request.form.get('name')
    muscle_group = request.form.get('muscle_group', 'Other')
    sets = request.form.get('sets')
    reps_min = request.form.get('reps_min')
    reps_max = request.form.get('reps_max')
    rest = request.form.get('rest_seconds')
    is_compound = 'is_compound' in request.form
    
    if not workout_day_id or not name or not sets or not reps_min or not reps_max or not rest:
        flash("Všetky polia sú povinné pre pridanie cviku.", "danger")
        return redirect(url_for('profile.training_settings'))
        
    try:
        count_res = supabase.table('program_exercises').select('id').eq('workout_day_id', workout_day_id).execute()
        order_index = len(count_res.data) if count_res.data else 0
        
        data = {
            'workout_day_id': workout_day_id,
            'name': name.strip(),
            'muscle_group': muscle_group.strip(),
            'sets_working': int(sets),
            'reps_min': int(reps_min),
            'reps_max': int(reps_max),
            'rest_seconds': int(rest),
            'is_compound': is_compound,
            'is_optional': False,
            'order_index': order_index
        }
        
        supabase.table('program_exercises').insert(data).execute()
        flash(f"Cvik '{name}' bol úspešne pridaný.", "success")
    except Exception as e:
        flash(f"Chyba pri pridaní cviku: {str(e)}", "danger")
        
    return redirect(url_for('profile.training_settings'))

@bp.route('/training/delete/<exercise_id>', methods=['POST'])
@login_required
def training_delete(exercise_id):
    try:
        supabase.table('program_exercises').delete().eq('id', exercise_id).execute()
        flash("Cvik bol úspešne odstránený.", "success")
    except Exception as e:
        flash(f"Chyba pri mazaní cviku: {str(e)}", "danger")
        
    return redirect(url_for('profile.training_settings'))
