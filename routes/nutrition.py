import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from routes import get_supabase, login_required

bp = Blueprint('nutrition', __name__, url_prefix='/nutrition')
supabase = get_supabase()

@bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    user_res = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    user = user_res.data[0] if user_res.data else {}
    
    today_date = datetime.date.today().isoformat()
    nut_res = supabase.table('nutrition_logs').select('*').eq('user_id', user_id).eq('date', today_date).order('created_at').execute()
    
    logs = nut_res.data if nut_res.data else []
    
    sum_cals = sum(log['calories'] for log in logs)
    sum_pro = sum(log['protein_g'] for log in logs)
    sum_carb = sum(log['carbs_g'] for log in logs)
    sum_fat = sum(log['fat_g'] for log in logs)
    
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    week_res = supabase.table('nutrition_logs').select('calories, date').eq('user_id', user_id).gte('date', week_ago).execute()
    
    avg_cal = 0
    if week_res.data:
        total_cals = sum(l['calories'] for l in week_res.data)
        dates_with_logs = len(set(l['date'] for l in week_res.data))
        dates_with_logs = dates_with_logs if dates_with_logs > 0 else 1
        avg_cal = round(total_cals / dates_with_logs)
        
    return render_template('nutrition.html', 
                          user=user, 
                          logs=logs,
                          sum_cals=sum_cals, sum_pro=round(sum_pro, 1), 
                          sum_carb=round(sum_carb, 1), sum_fat=round(sum_fat, 1),
                          avg_cal=avg_cal)

@bp.route('/add', methods=['POST'])
@login_required
def add():
    user_id = session['user_id']
    data = {
        'user_id': user_id,
        'date': datetime.date.today().isoformat(),
        'calories': int(request.form.get('calories', '').strip() or 0),
        'protein_g': float(request.form.get('protein_g', '').strip() or 0),
        'carbs_g': float(request.form.get('carbs_g', '').strip() or 0),
        'fat_g': float(request.form.get('fat_g', '').strip() or 0)
    }
    supabase.table('nutrition_logs').insert(data).execute()
    flash("Jedlo bolo pridané.", "success")
    return redirect(url_for('nutrition.index'))

@bp.route('/edit-goals', methods=['POST'])
@login_required
def edit_goals():
    user_id = session['user_id']
    data = {
        'calories_target': int(request.form.get('calories_target')),
        'protein_target_g': float(request.form.get('protein_target_g')),
        'carb_target_g': float(request.form.get('carb_target_g')),
        'fat_target_g': float(request.form.get('fat_target_g'))
    }
    supabase.table('users').update(data).eq('id', user_id).execute()
    flash("Nový nutričný cieľ bol upravený.", "success")
    return redirect(url_for('nutrition.index'))

@bp.route('/delete/<id>')
@login_required
def delete(id):
    supabase.table('nutrition_logs').delete().eq('id', id).execute()
    flash("Záznam o jedle bol zmazaný.", "info")
    return redirect(url_for('nutrition.index'))

@bp.route('/api/chart_data')
@login_required
def chart_data():
    user_id = session['user_id']
    
    # Získame všetky záznamy usera
    res = supabase.table('nutrition_logs').select('date, calories, protein_g, carbs_g, fat_g').eq('user_id', user_id).order('date').execute()
    logs = res.data if res.data else []
    
    # Zoskupíme podľa dátumu
    daily_data = {}
    for log in logs:
        date = log['date']
        if date not in daily_data:
            daily_data[date] = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0}
            
        daily_data[date]['calories'] += log['calories']
        daily_data[date]['protein_g'] += log['protein_g']
        daily_data[date]['carbs_g'] += log['carbs_g']
        daily_data[date]['fat_g'] += log['fat_g']
        
    # Vytvoríme polia pre graf
    labels = sorted(daily_data.keys())
    cals = [daily_data[d]['calories'] for d in labels]
    pro = [round(daily_data[d]['protein_g'], 1) for d in labels]
    carb = [round(daily_data[d]['carbs_g'], 1) for d in labels]
    fat = [round(daily_data[d]['fat_g'], 1) for d in labels]
    
    return {
        'labels': labels,
        'calories': cals,
        'protein_g': pro,
        'carbs_g': carb,
        'fat_g': fat
    }
