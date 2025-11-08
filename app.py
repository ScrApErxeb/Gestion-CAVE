from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, ParametresGlobaux
import secrets
import os
import webbrowser
from threading import Timer

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/cave.db'
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
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
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

# Routes principales
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, actif=True).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Bienvenue {user.nom_complet or user.username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Identifiants incorrects', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie', 'info')
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime, timedelta
    from models import Produit, Abonne, Facture, Consommation
    from sqlalchemy import func
    
    # Statistiques générales
    stats = {
        'total_produits': Produit.query.filter_by(actif=True).count(),
        'total_abonnes': Abonne.query.filter_by(actif=True).count(),
        'produits_stock_critique': Produit.query.filter(Produit.stock <= Produit.stock_alerte).count(),
    }
    
    # Statistiques du jour
    aujourd_hui = datetime.now().date()
    debut_jour = datetime.combine(aujourd_hui, datetime.min.time())
    
    ventes_jour = db.session.query(func.sum(Consommation.montant_total)).filter(
        Consommation.date >= debut_jour
    ).scalar() or 0
    
    factures_impayees = db.session.query(func.sum(Facture.montant_ttc)).filter(
        Facture.statut.in_(['impayee', 'partielle'])
    ).scalar() or 0
    
    stats['ventes_jour'] = ventes_jour
    stats['factures_impayees'] = factures_impayees
    
    # Produits en stock critique
    produits_critiques = Produit.query.filter(
        Produit.stock <= Produit.stock_alerte,
        Produit.actif == True
    ).limit(10).all()
    
    # Dernières consommations
    dernieres_conso = Consommation.query.order_by(Consommation.date.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         stats=stats,
                         produits_critiques=produits_critiques,
                         dernieres_conso=dernieres_conso)

@app.route('/abonnes')
@login_required
def abonnes():
    return render_template('abonnes.html')

@app.route('/consommations')
@login_required
def consommations():
    return render_template('consommations.html')

@app.route('/factures')
@login_required
def factures():
    return render_template('factures.html')

@app.route('/paiements')
@login_required
def paiements():
    return render_template('paiements.html')

@app.route('/produits')
@login_required
def produits():
    return render_template('produits.html')

@app.route('/stock')
@login_required
def stock():
    return render_template('stock.html')

# Gestionnaire d'erreurs
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Enregistrement des blueprints (routes API)
def register_blueprints():
    from routes.api_abonnes import abonnes_bp
    from routes.api_produits import produits_bp
    from routes.api_factures import factures_bp
    from routes.api_paiements import paiements_bp
    from routes.api_consommations import consommations_bp
    from routes.api_stock import stock_bp
    
    app.register_blueprint(abonnes_bp, url_prefix='/api')
    app.register_blueprint(produits_bp, url_prefix='/api')
    app.register_blueprint(factures_bp, url_prefix='/api')
    app.register_blueprint(paiements_bp, url_prefix='/api')
    app.register_blueprint(consommations_bp, url_prefix='/api')
    app.register_blueprint(stock_bp, url_prefix='/api')

def open_browser():
    """Ouvre le navigateur automatiquement"""
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Créer le dossier database s'il n'existe pas
    os.makedirs('database', exist_ok=True)
    
    # Initialiser la base de données
    init_database()
    
    # Enregistrer les routes API
    register_blueprints()
    
    # Ouvrir le navigateur après 1 seconde
    Timer(1, open_browser).start()
    
    print("=" * 50)
    print("🍷 CAVE GESTION - Serveur démarré")
    print("=" * 50)
    print("📍 URL: http://127.0.0.1:5000/")
    print("👤 Utilisateur: admin")
    print("🔑 Mot de passe: admin123")
    print("=" * 50)
    print("Appuyez sur CTRL+C pour arrêter le serveur")
    print("=" * 50)
    
    app.run(debug=True, use_reloader=False)