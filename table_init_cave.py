import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join("database", "app.db")

# --- Création du dossier database s’il n’existe pas ---
os.makedirs("database", exist_ok=True)

# --- Connexion SQLite ---
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# --- Dictionnaire des tables SQL ---
tables = {
    "utilisateurs": """
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_utilisateur TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            derniere_connexion DATETIME
        );
    """,
    "fournisseurs": """
        CREATE TABLE IF NOT EXISTS fournisseurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            contact TEXT,
            adresse TEXT,
            note TEXT
        );
    """,
    "produits": """
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            type TEXT CHECK (type IN ('vin','biere','sucrerie','autre')),
            prix_achat REAL NOT NULL,
            prix_vente REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            fournisseur_id INTEGER,
            date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id)
        );
    """,
    "abonnes": """
        CREATE TABLE IF NOT EXISTS abonnes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_abonne TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            telephone TEXT NOT NULL,
            date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'actif'
        );
    """,
    "consommations": """
        CREATE TABLE IF NOT EXISTS consommations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abonne_id INTEGER NOT NULL,
            produit_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL,
            date_consommation DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (abonne_id) REFERENCES abonnes(id),
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        );
    """,
    "factures": """
        CREATE TABLE IF NOT EXISTS factures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_facture TEXT UNIQUE NOT NULL,
            abonne_id INTEGER,
            date_facture DATETIME DEFAULT CURRENT_TIMESTAMP,
            montant_total REAL NOT NULL,
            statut TEXT DEFAULT 'en_attente',
            FOREIGN KEY (abonne_id) REFERENCES abonnes(id)
        );
    """,
    "paiements": """
        CREATE TABLE IF NOT EXISTS paiements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facture_id INTEGER NOT NULL,
            date_paiement DATETIME DEFAULT CURRENT_TIMESTAMP,
            montant REAL NOT NULL,
            mode TEXT CHECK (mode IN ('especes','carte','mobile_money')),
            FOREIGN KEY (facture_id) REFERENCES factures(id)
        );
    """,
    "compta": """
        CREATE TABLE IF NOT EXISTS compta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT CHECK (type IN ('recette','depense')) NOT NULL,
            montant REAL NOT NULL,
            reference TEXT,
            date_operation DATETIME DEFAULT CURRENT_TIMESTAMP,
            commentaire TEXT
        );
    """,
    "mouvements_stock": """
        CREATE TABLE IF NOT EXISTS mouvements_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            type_mouvement TEXT CHECK (type_mouvement IN ('ENTREE_INITIALE','ENTREE','SORTIE','AJUSTEMENT')) NOT NULL,
            quantite INTEGER NOT NULL,
            motif TEXT NOT NULL,
            date_mouvement DATETIME DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (produit_id) REFERENCES produits(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        );
    """,
    "journal_log": """
        CREATE TABLE IF NOT EXISTS journal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER,
            action TEXT NOT NULL,
            description TEXT,
            date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'succes',
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        );
    """
}

# --- Création des tables ---
for name, sql in tables.items():
    cur.execute(sql)

# --- Création du compte admin par défaut ---
cur.execute("SELECT COUNT(*) FROM utilisateurs;")
if cur.fetchone()[0] == 0:
    password_hash = hashlib.sha256("admin".encode()).hexdigest()
    cur.execute("""
        INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, role)
        VALUES (?, ?, ?)
    """, ("admin", password_hash, "admin"))
    print("[OK] Utilisateur 'admin' créé (mot de passe = admin)")

conn.commit()
conn.close()
print(f"[OK] Base initialisée ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) -> {DB_PATH}")
