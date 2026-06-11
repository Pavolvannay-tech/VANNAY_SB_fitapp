from flask import Flask, redirect, url_for
from flask_session import Session
from config import Config
from routes import auth, onboarding, dashboard, workout, progress, nutrition, profile
import os

app = Flask(__name__)
app.config.from_object(Config)

# Inicializácia session manažéra (uloženie session dát lokálne pre testovanie). 
# Pri produkcii je lepšie zvoliť Redis, databázu a pod.
Session(app)

app.register_blueprint(auth.bp)
app.register_blueprint(onboarding.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(workout.bp)
app.register_blueprint(progress.bp)
app.register_blueprint(nutrition.bp)
app.register_blueprint(profile.bp)

@app.route('/')
def index():
    return redirect(url_for('dashboard.index'))

if __name__ == '__main__':
    # host='0.0.0.0' umožní prístup k aplikácii z akéhokoľvek zariadenia v tvojej lokálnej sieti
    app.run(debug=True, host='0.0.0.0', port=8080)
