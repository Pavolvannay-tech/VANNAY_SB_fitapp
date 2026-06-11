from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes import get_supabase

bp = Blueprint('auth', __name__)
supabase = get_supabase()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user_id'] = auth_response.user.id
            session['email'] = auth_response.user.email
            
            # Fetch user details to check onboarding status
            user_data = supabase.table('users').select('*').eq('id', auth_response.user.id).limit(1).execute()
            if user_data.data:
                user_row = user_data.data[0]
                session['name'] = user_row.get('name')
                session['onboarding_done'] = user_row.get('onboarding_done', False)
                if session['onboarding_done']:
                    return redirect(url_for('dashboard.index'))
                else:
                    return redirect(url_for('onboarding.step1'))
            else:
                session['onboarding_done'] = False
                return redirect(url_for('onboarding.step1'))
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash(f"Chyba prihlásenia: {str(e)}", "danger")
            
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            auth_response = supabase.auth.sign_up({"email": email, "password": password})
            if auth_response.user:
                session['user_id'] = auth_response.user.id
                session['email'] = auth_response.user.email
                session['onboarding_done'] = False
                
                # Zabezpečenie existencie riadku v public.users ak chýba DB trigger
                # Zistíme, či používateľ existuje
                try:
                    exists = supabase.table('users').select('id').eq('id', auth_response.user.id).execute()
                    if not exists.data:
                        supabase.table('users').insert({
                            'id': auth_response.user.id,
                            'email': email,
                            'onboarding_done': False
                        }).execute()
                except Exception:
                    pass
                    
                flash("Registrácia úspešná, vitaj!", "success")
                return redirect(url_for('onboarding.step1'))
        except Exception as e:
            flash(f"Chyba pri registrácii: {str(e)}", "danger")
            
    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash("Bol si úspešne odhlásený.", "info")
    return redirect(url_for('auth.login'))
