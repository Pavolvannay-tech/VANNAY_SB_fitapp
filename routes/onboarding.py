from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes import get_supabase, login_required
from nutrition import calculate_macros
from program_generator import generate_program

bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')
supabase = get_supabase()

@bp.route('/1', methods=['GET', 'POST'])
@login_required
def step1():
    if request.method == 'POST':
        name = request.form.get('name')
        age_raw = request.form.get('age')
        gender = request.form.get('gender')
        weight_raw = request.form.get('weight_kg')
        height_raw = request.form.get('height_cm')
        
        if not all([name, age_raw, gender, weight_raw, height_raw]):
            flash("Nie sú vyplnené všetky údaje.", "danger")
            return redirect(url_for('onboarding.step1'))
            
        try:
            data = {
                'name': name,
                'age': int(age_raw),
                'gender': gender,
                'weight_kg': float(weight_raw),
                'height_cm': float(height_raw)
            }
            supabase.table('users').update(data).eq('id', session['user_id']).execute()
            return redirect(url_for('onboarding.step2'))
        except (ValueError, TypeError):
            flash("Nie sú vyplnené všetky údaje.", "danger")
            return redirect(url_for('onboarding.step1'))
    return render_template('onboarding/step1.html')

@bp.route('/2', methods=['GET', 'POST'])
@login_required
def step2():
    if request.method == 'POST':
        experience = request.form.get('experience')
        training_days_raw = request.form.get('training_days')
        session_duration_raw = request.form.get('session_duration')
        
        if not all([experience, training_days_raw, session_duration_raw]):
            flash("Nie sú vyplnené všetky údaje.", "danger")
            return redirect(url_for('onboarding.step2'))
            
        try:
            data = {
                'experience': experience,
                'training_days': int(training_days_raw),
                'session_duration': int(session_duration_raw)
            }
            supabase.table('users').update(data).eq('id', session['user_id']).execute()
            return redirect(url_for('onboarding.step3'))
        except (ValueError, TypeError):
            flash("Nie sú vyplnené všetky údaje.", "danger")
            return redirect(url_for('onboarding.step2'))
    return render_template('onboarding/step2.html')

@bp.route('/3', methods=['GET', 'POST'])
@login_required
def step3():
    if request.method == 'POST':
        fields = [
            'exercise_chest_flat', 'exercise_chest_incline',
            'exercise_back_vertical', 'exercise_back_horizontal_wide',
            'exercise_back_horizontal_close', 'exercise_shoulders',
            'exercise_triceps', 'exercise_biceps',
            'exercise_quads', 'exercise_hamstrings'
        ]
        
        data = {}
        missing = False
        for f in fields:
            val = request.form.get(f)
            if not val:
                missing = True
            data[f] = val
            
        if missing:
            flash("Nie sú vyplnené všetky údaje.", "danger")
            return redirect(url_for('onboarding.step3'))
            
        supabase.table('users').update(data).eq('id', session['user_id']).execute()
        return redirect(url_for('onboarding.step4'))
    return render_template('onboarding/step3.html')

@bp.route('/4', methods=['GET', 'POST'])
@login_required
def step4():
    if request.method == 'POST':
        data = {
            'wants_rear_delts': 'wants_rear_delts' in request.form,
            'wants_brachialis': 'wants_brachialis' in request.form,
            'wants_adduction': 'wants_adduction' in request.form,
            'wants_abs': 'wants_abs' in request.form,
            'wants_calves': 'wants_calves' in request.form,
            'wants_forearms': 'wants_forearms' in request.form
        }
        supabase.table('users').update(data).eq('id', session['user_id']).execute()
        return redirect(url_for('onboarding.step5'))
    return render_template('onboarding/step4.html')

@bp.route('/5', methods=['GET', 'POST'])
@login_required
def step5():
    if request.method == 'POST':
        activity_level = request.form.get('activity_level')
        goal = request.form.get('goal')
        
        if not activity_level or not goal:
            flash("Nie sú vyplnené všetky údaje.", "danger")
            return redirect(url_for('onboarding.step5'))
        
        user_res = supabase.table('users').select('*').eq('id', session['user_id']).limit(1).execute()
        
        if not user_res.data:
            print(f"Warning: User {session['user_id']} not found in public.users table during step 5. Creating them now.")
            supabase.table('users').insert({
                'id': session['user_id'],
                'email': session.get('email', ''),
                'onboarding_done': False
            }).execute()
            user_res = supabase.table('users').select('*').eq('id', session['user_id']).limit(1).execute()

        user = user_res.data[0]
        
        # Fallback pre prípad, že v krokoch 1-4 chýbali dáta a updaty zlyhali
        weight = user.get('weight_kg') or 70.0
        height = user.get('height_cm') or 170.0
        age = user.get('age') or 25
        gender = user.get('gender') or 'male'
        
        macros = calculate_macros(
            weight, height, age, 
            gender, activity_level, goal
        )
        
        data = {
            'activity_level': activity_level,
            'goal': goal,
            'tdee_calculated': macros['tdee'],
            'calories_target': macros['calories'],
            'protein_target_g': macros['protein'],
            'fat_target_g': macros['fat'],
            'carb_target_g': macros['carbs'],
            'onboarding_done': True
        }
        supabase.table('users').update(data).eq('id', session['user_id']).execute()
        session['onboarding_done'] = True
        
        generate_program(session['user_id'], supabase)
        
        return redirect(url_for('dashboard.index'))
    return render_template('onboarding/step5.html')
