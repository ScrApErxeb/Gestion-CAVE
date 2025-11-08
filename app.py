import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from core.utilisateurs import verifier_connexion, verifier_session
from models import db, User
import threading, webbrowser
from routes.api import api_bp
from routes.api_abonnes import api_abonnes



app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cave.db")

if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "cle_temporaire"
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(api_abonnes)


db.init_app(app)

# --- ROUTE LOGIN ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.form
    user = verifier_connexion(data.get('username'), data.get('password'))
    print("Résultat connexion :", user)
    if user:
        token = user['token']
        session['token'] = token
        return redirect(url_for('home'))
    return render_template('login.html', error="Identifiants invalides")


from flask import jsonify
from models import Abonne

@app.route('/api/abonnes')
def api_abonnes():
    abonnes = Abonne.query.all()
    data = [
        {
            "id": a.id,
            "nom": a.nom,
            "prenom": a.prenom,
            "adresse": a.adresse,
            "telephone": a.telephone
        }
        for a in abonnes
    ]
    return jsonify(data)




# --- ROUTE PRINCIPALE ---
@app.route('/home')
def home():
    token = session.get('token')
    user_id = verifier_session(token)
    if not user_id:
        session.pop('token', None)
        return redirect('/')
    return render_template('home.html')

# --- ROUTES ONGLET ---
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/abonnes')
def abonnes():
    return render_template('abonnes.html')

@app.route('/consommations')
def consommations():
    return render_template('consommations.html')

@app.route('/factures')
def factures():
    return render_template('factures.html')

@app.route('/paiements')
def paiements():
    return render_template('paiements.html')

# --- API test ---
@app.route('/api/ping')
def ping():
    return jsonify({"status": "ok"})

# --- Lancement auto navigateur ---
def _lancer_nav():
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    threading.Timer(1, _lancer_nav).start()
    app.run(debug=False)
