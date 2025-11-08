from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur avec authentification"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='caissier')  # admin, caissier, gestionnaire
    nom_complet = db.Column(db.String(100))
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    factures_creees = db.relationship('Facture', backref='createur', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, action):
        permissions = {
            'admin': ['all'],
            'caissier': ['ventes', 'consommations', 'paiements', 'view_abonnes'],
            'gestionnaire': ['abonnes', 'produits', 'factures', 'stock', 'rapports']
        }
        return 'all' in permissions.get(self.role, []) or action in permissions.get(self.role, [])


class Categorie(db.Model):
    """Catégories de produits"""
    __tablename__ = 'categorie'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relations
    produits = db.relationship('Produit', backref='categorie', lazy=True)


class Fournisseur(db.Model):
    """Fournisseurs de produits"""
    __tablename__ = 'fournisseur'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    email = db.Column(db.String(100))
    
    # Relations
    produits = db.relationship('Produit', backref='fournisseur', lazy=True)


class Produit(db.Model):
    """Produits en vente"""
    __tablename__ = 'produit'
    
    id = db.Column(db.Integer, primary_key=True)
    code_produit = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))  # boisson, alcool, snack, etc.
    prix_achat = db.Column(db.Float, nullable=False)
    prix_vente = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_alerte = db.Column(db.Integer, default=10)
    unite = db.Column(db.String(20), default='unité')  # unité, carton, bouteille
    categorie_id = db.Column(db.Integer, db.ForeignKey('categorie.id'))
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur.id'))
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    consommations = db.relationship('Consommation', backref='produit', lazy=True)
    mouvements_stock = db.relationship('StockLog', backref='produit', lazy=True)
    
    @property
    def marge(self):
        return self.prix_vente - self.prix_achat
    
    @property
    def marge_pourcentage(self):
        if self.prix_achat > 0:
            return ((self.prix_vente - self.prix_achat) / self.prix_achat) * 100
        return 0
    
    @property
    def stock_critique(self):
        return self.stock <= self.stock_alerte


class Abonne(db.Model):
    """Abonnés de la cave"""
    __tablename__ = 'abonne'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_abonne = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    limite_credit = db.Column(db.Float, default=0)  # Limite de crédit autorisée
    
    # Relations
    consommations = db.relationship('Consommation', backref='abonne', lazy=True)
    factures = db.relationship('Facture', backref='abonne', lazy=True)
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom or ''}".strip()
    
    @property
    def solde_du(self):
        """Calcul du solde dû (factures impayées)"""
        total_factures = sum(f.montant_ttc for f in self.factures if f.statut != 'payee')
        total_paiements = sum(p.montant for f in self.factures for p in f.paiements)
        return total_factures - total_paiements


class Consommation(db.Model):
    """Enregistrement des consommations"""
    __tablename__ = 'consommation'
    
    id = db.Column(db.Integer, primary_key=True)
    abonne_id = db.Column(db.Integer, db.ForeignKey('abonne.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)
    montant_total = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    facture_id = db.Column(db.Integer, db.ForeignKey('facture.id'))
    note = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(Consommation, self).__init__(**kwargs)
        if not self.prix_unitaire and self.produit:
            self.prix_unitaire = self.produit.prix_vente
        if not self.montant_total:
            self.montant_total = self.quantite * self.prix_unitaire


class Facture(db.Model):
    """Factures émises"""
    __tablename__ = 'facture'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_facture = db.Column(db.String(20), unique=True, nullable=False)
    abonne_id = db.Column(db.Integer, db.ForeignKey('abonne.id'), nullable=False)
    montant_ht = db.Column(db.Float, default=0)
    taux_tva = db.Column(db.Float, default=18.0)  # TVA Burkina Faso
    montant_tva = db.Column(db.Float, default=0)
    montant_ttc = db.Column(db.Float, default=0)
    statut = db.Column(db.String(20), default='impayee')  # impayee, partielle, payee
    date_emission = db.Column(db.DateTime, default=datetime.utcnow)
    date_echeance = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    note = db.Column(db.Text)
    
    # Relations
    consommations = db.relationship('Consommation', backref='facture', lazy=True)
    paiements = db.relationship('Paiement', backref='facture', lazy=True, cascade='all, delete-orphan')
    
    def calculer_montants(self):
        """Calcul automatique des montants HT, TVA et TTC"""
        self.montant_ht = sum(c.montant_total for c in self.consommations)
        self.montant_tva = self.montant_ht * (self.taux_tva / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva
    
    @property
    def montant_paye(self):
        return sum(p.montant for p in self.paiements)
    
    @property
    def reste_a_payer(self):
        return self.montant_ttc - self.montant_paye
    
    def mettre_a_jour_statut(self):
        """Mise à jour automatique du statut selon les paiements"""
        if self.montant_paye >= self.montant_ttc:
            self.statut = 'payee'
        elif self.montant_paye > 0:
            self.statut = 'partielle'
        else:
            self.statut = 'impayee'


class Paiement(db.Model):
    """Paiements reçus"""
    __tablename__ = 'paiement'
    
    id = db.Column(db.Integer, primary_key=True)
    facture_id = db.Column(db.Integer, db.ForeignKey('facture.id'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    mode_paiement = db.Column(db.String(20), nullable=False)  # especes, mobile_money, cheque, carte
    reference = db.Column(db.String(50))  # Référence transaction
    date_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    recu_par = db.Column(db.String(100))
    note = db.Column(db.Text)


class StockLog(db.Model):
    """Journal des mouvements de stock"""
    __tablename__ = 'stock_log'
    
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'), nullable=False)
    type_mouvement = db.Column(db.String(20), nullable=False)  # entree, sortie, ajustement, inventaire
    quantite = db.Column(db.Integer, nullable=False)
    stock_avant = db.Column(db.Integer)
    stock_apres = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur = db.Column(db.String(50))
    commentaire = db.Column(db.Text)
    reference = db.Column(db.String(50))  # Référence bon de commande, facture fournisseur, etc.


class ParametresGlobaux(db.Model):
    """Paramètres de configuration de la cave"""
    __tablename__ = 'parametres_globaux'
    
    id = db.Column(db.Integer, primary_key=True)
    nom_cave = db.Column(db.String(100), default='Ma Cave')
    adresse = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    ifu = db.Column(db.String(50))  # Identifiant Fiscal Unique
    rccm = db.Column(db.String(50))  # Registre du Commerce
    taux_tva_defaut = db.Column(db.Float, default=18.0)
    devise = db.Column(db.String(10), default='FCFA')
    logo = db.Column(db.LargeBinary)  # Logo en binaire


class AuditLog(db.Model):
    """Journal d'audit des actions utilisateurs"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    utilisateur = db.Column(db.String(50))
    action = db.Column(db.String(100))
    table_concernee = db.Column(db.String(50))
    enregistrement_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    adresse_ip = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)