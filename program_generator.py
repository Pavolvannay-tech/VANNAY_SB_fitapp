import uuid

def generate_program(user_id, supabase):
    # 1. Načítaj usera
    user_res = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    if not user_res.data:
        return None
    user = user_res.data[0]
        
    # 2. Deaktivuj staré programy pre tohto používateľa
    supabase.table('programs').update({'is_active': False}).eq('user_id', user_id).execute()
    
    # 3. Urči konfiguráciu splity na základe dní a dĺžky tréningu
    training_days = user.get('training_days', 3)
    session_duration = user.get('session_duration', 90)
    S = 3 if session_duration == 120 else 2
    
    split_map = {
        2: "FB-FB",
        3: "U-L-FB",
        4: "ULUL",
        5: "ULRPPLR"
    }
    split_type = split_map.get(training_days, "U-L-FB")
    
    # 4. Vytvor nový program
    program_res = supabase.table('programs').insert({
        'user_id': user_id,
        'split_type': split_type,
        'is_active': True
    }).execute()
    program_id = program_res.data[0]['id']
    
    # 5. Definícia tréningových dní v týždni
    days_config = {
        "FB-FB": [(0, "Full Body"), (3, "Full Body")],
        "U-L-FB": [(0, "Upper"), (2, "Lower"), (4, "Full Body")],
        "ULUL": [(0, "Upper"), (1, "Lower"), (3, "Upper"), (4, "Lower")],
        "ULRPPLR": [(0, "Upper"), (1, "Lower"), (3, "Push"), (4, "Pull"), (5, "Legs")]
    }
    
    workout_days_insert = []
    days = days_config.get(split_type, days_config["U-L-FB"])
    for idx, (dow, dtype) in enumerate(days):
        workout_days_insert.append({
            'program_id': program_id,
            'day_of_week': dow,
            'day_type': dtype,
            'order_index': idx
        })
        
    wd_res = supabase.table('workout_days').insert(workout_days_insert).execute()
    workout_days = wd_res.data
    
    # 6. Preferencie cvikov načítané z profilu používateľa
    chest_flat = user.get('exercise_chest_flat') or "Flat Bench Press"
    chest_incline = user.get('exercise_chest_incline') or "Incline Barbell Press"
    back_vert = user.get('exercise_back_vertical') or "Lat Pulldown"
    back_wide = user.get('exercise_back_horizontal_wide') or "Barbell Row"
    back_close = user.get('exercise_back_horizontal_close') or "Cable Row"
    shoulders = user.get('exercise_shoulders') or "Overhead Barbell Press"
    triceps = user.get('exercise_triceps') or "Triceps Pulldown"
    biceps = user.get('exercise_biceps') or "Barbell Curl"
    quads = user.get('exercise_quads') or "Squat"
    hamstrings = user.get('exercise_hamstrings') or "Romanian Deadlift"
    
    # Voliteľné svalové partie (izolácie)
    wants_rear = user.get('wants_rear_delts', False)
    wants_brach = user.get('wants_brachialis', False)
    wants_add = user.get('wants_adduction', False)
    wants_abs = user.get('wants_abs', False)
    wants_calves = user.get('wants_calves', False)
    wants_forearms = user.get('wants_forearms', False)
    
    exercises_to_insert = []
    
    # 7. Generovanie cvikov do dní
    for wd in workout_days:
        wd_id = wd['id']
        dtype = wd['day_type']
        
        template = []
        
        if dtype == "Upper":
            template = [
                (chest_flat, 'chest', True, 2, 6, 8, 240, False),
                (back_vert, 'lats', True, 2, 6, 8, 240, False),
                (shoulders, 'shoulders', True, 2, 6, 8, 240, False),
                (back_wide, 'upper back', True, 2, 6, 8, 240, False),
                (chest_incline, 'upper chest', True, 1, 8, 10, 240, False),
                (back_close, 'lats', True, 1, 8, 10, 240, False),
                ("Lateral Raises", 'mid delts', False, 1, 10, 15, 180, False),
                (triceps, 'triceps', False, 2, 8, 12, 180, False),
                (biceps, 'biceps', False, 2, 8, 12, 180, False)
            ]
            if wants_rear: template.append(("Face Pull / Rear Delt Fly", 'rear delts', False, 1, 10, 15, 180, True))
            if wants_brach: template.append(("Hammer Curl", 'brachialis', False, 1, 8, 12, 180, True))
            
        elif dtype == "Lower":
            template = [
                (quads, 'quads', True, S, 6, 8, 240, False),
                (hamstrings, 'hamstrings', True, S, 6, 8, 240, False),
                ("Leg Extensions", 'quads', False, 2 if S==3 else 1, 10, 15, 180, False),
                ("Lying Hamstring Curl", 'hamstrings', False, 2 if S==3 else 1, 10, 15, 180, False)
            ]
            if wants_abs: template.append(("Ab Crunches", 'abs', False, 2, 10, 20, 180, True))
            if wants_calves: template.append(("Calf Raises", 'calves', False, 2, 10, 20, 180, True))
            if wants_add: template.append(("Leg Adduction", 'adductors', False, 1, 12, 15, 180, True))
            if wants_forearms: template.append(("Inner Forearm Curl", 'forearms', False, 2, 12, 15, 180, True))

        elif dtype == "Push":
            template = [
                (chest_flat, 'chest', True, S, 6, 8, 240, False),
                (chest_incline, 'upper chest', True, 2, 8, 10, 240, False),
                (shoulders, 'shoulders', True, S, 6, 8, 240, False),
                ("Lateral Raises", 'mid delts', False, 2 if S==3 else 1, 10, 15, 180, False),
                (triceps, 'triceps', False, S, 8, 12, 180, False),
                ("Skull Crushers", 'triceps', False, 2 if S==3 else 1, 10, 15, 180, False)
            ]
            if wants_rear: template.append(("Face Pull / Rear Delt Fly", 'rear delts', False, 1, 10, 15, 180, True))

        elif dtype == "Pull":
            template = [
                (back_wide, 'upper back', True, S, 6, 8, 240, False),
                (back_vert, 'lats', True, S, 6, 8, 240, False),
                (back_close, 'lats', True, 2, 8, 10, 240, False),
                (biceps, 'biceps', False, S, 8, 12, 180, False),
                ("Hammer Curls", 'biceps', False, 2 if S==3 else 1, 8, 12, 180, False)
            ]
            if wants_forearms: template.append(("Inner Forearm Curl", 'forearms', False, 2, 12, 15, 180, True))

        elif dtype == "Legs":
            template = [
                (quads, 'quads', True, S, 6, 8, 240, False),
                (hamstrings, 'hamstrings', True, S, 6, 8, 240, False),
                ("Leg Extensions", 'quads', False, 2, 10, 15, 180, False),
                ("Lying Hamstring Curl", 'hamstrings', False, 2, 10, 15, 180, False)
            ]
            if wants_calves: template.append(("Calf Raises", 'calves', False, 2, 10, 20, 180, True))
            if wants_abs: template.append(("Ab Crunches", 'abs', False, 2, 10, 20, 180, True))
            if wants_add: template.append(("Leg Adduction", 'adductors', False, 1, 12, 15, 180, True))

        elif dtype == "Full Body":
            template = [
                (chest_flat, 'chest', True, 2, 6, 8, 240, False),
                (back_vert, 'lats', True, 2, 6, 8, 240, False),
                (shoulders, 'shoulders', True, 2, 6, 8, 240, False),
                (back_wide, 'upper back', True, 2, 6, 8, 240, False),
                (quads, 'quads', True, 2, 6, 8, 240, False),
                (hamstrings, 'hamstrings', True, 2, 6, 8, 240, False),
                (triceps, 'triceps', False, 1, 8, 12, 180, False),
                (biceps, 'biceps', False, 1, 8, 12, 180, False)
            ]
            if wants_rear: template.append(("Face Pull / Rear Delt Fly", 'rear delts', False, 1, 10, 15, 180, True))
            if wants_abs: template.append(("Ab Crunches", 'abs', False, 2, 10, 20, 180, True))
            if wants_calves: template.append(("Calf Raises", 'calves', False, 2, 10, 20, 180, True))

        for opt_idx, t_item in enumerate(template):
            exercises_to_insert.append({
                'workout_day_id': wd_id,
                'name': t_item[0],
                'muscle_group': t_item[1],
                'is_compound': t_item[2],
                'sets_working': t_item[3],
                'reps_min': t_item[4],
                'reps_max': t_item[5],
                'rest_seconds': t_item[6],
                'is_optional': t_item[7],
                'order_index': opt_idx
            })
            
    if exercises_to_insert:
        supabase.table('program_exercises').insert(exercises_to_insert).execute()
        
    return program_id
