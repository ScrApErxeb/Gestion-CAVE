from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, ParametresGlobaux
import secrets 
import os
import webbrowser
from threading import Timer

app = Flask(__name__)



# --- Configuration ---
if not os.path.exists("database"):
    os.makedirs("database")


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cave.db")

app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Création des tables et données initiales
def init_database():
    with app.app_context():
        db.create_all()
        
        # Créer utilisateur admin par défaut si aucun utilisateur n'existe
        if User.query.count() == 0:
            admin = User(
                username='admin',
                role='admin',
                nom_complet='Administrateur'
            ),
            vendeur = User(
                username='vendeur',
                role='vendeur',
                nom_complet='Vendeur')


            admin.set_password('admin123')
            vendeur.set_password('vendeur123')

            db.session.add(admin)
            db.session.add(vendeur)

            # Paramètres par défaut
            params = ParametresGlobaux(
                nom_cave='Cave Gestion',
                devise='FCFA',
                taux_tva_defaut=18.0
            )
            db.session.add(params)
            
            db.session.commit()
            print("✓ Base de données initialisée")
            print("✓ Utilisateur admin créé (admin/admin123)")

