def calculate_macros(weight_kg, height_cm, age, gender, activity_level, goal):
    """
    Vypočíta TDEE (Mifflin-St Jeor) a rozvrhne makronutrienty (bielkoviny, tuky, sacharidy)
    podľa tréningového cieľa používateľa.
    """
    # 1. BMR - Bazálny metabolizmus (Mifflin-St Jeor)
    if gender == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # female
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
    # 2. Faktor aktivity
    activity_factors = {
        'sedentary': 1.2,
        'moderate': 1.375,
        'active': 1.55
    }
    factor = activity_factors.get(activity_level, 1.2)
    tdee = int(bmr * factor)
    
    # 3. Úprava podľa cieľa
    target_calories = tdee
    if goal == 'bulk':
        target_calories += 250
    elif goal == 'cut':
        target_calories -= 400
        
    # 4. Rozloženie makronutrientov (v gramoch)
    # Bielkoviny (1.8g na kg váhy - vedecky podložené pre hypertrofiu)
    protein_g = round(weight_kg * 1.8, 1)
    
    # Tuky (0.8g na kg váhy - podporené kvôli hladine hormónov a testosterónu u naturálov)
    fat_g = round(weight_kg * 0.8, 1)
    
    # Sacharidy (Zvyšok kalórií)
    protein_cals = protein_g * 4
    fat_cals = fat_g * 9
    carbs_cals = target_calories - protein_cals - fat_cals
    carb_g = round(carbs_cals / 4, 1) if carbs_cals > 0 else 0
    
    return {
        'tdee': tdee,
        'calories': target_calories,
        'protein': protein_g,
        'fat': fat_g,
        'carbs': carb_g
    }
