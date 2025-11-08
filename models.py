from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Abonne(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True)
    nom = db.Column(db.String(50))
    telephone = db.Column(db.String(20))

    def to_dict(self):
        return {
            "id": self.id,
            "numero_abonne": self.numero_abonne,
            "nom": self.nom,
            "telephone": self.telephone,
            "date_creation": self.date_creation.isoformat()
        }

    def __repr__(self):
        return f"<Abonne {self.nom}>"


class Produit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50))
    type = db.Column(db.String(20))  # vin, bière, sucrerie
    prix_achat = db.Column(db.Float)
    prix_vente = db.Column(db.Float)
    stock = db.Column(db.Integer)
    fournisseur = db.Column(db.String(50))


class Vente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    abonne_id = db.Column(db.Integer, db.ForeignKey("abonne.id"))
    produit_id = db.Column(db.Integer, db.ForeignKey("produit.id"))
    quantite = db.Column(db.Integer)
    total = db.Column(db.Float)


class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    montant = db.Column(db.Float)
    mode = db.Column(db.String(20))  # espèces, mobile money
    vente_id = db.Column(db.Integer, db.ForeignKey("vente.id"))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)