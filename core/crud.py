# core/crud.py
import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join("database", "app.db")

# --- Tables autorisées ---
TABLES_VALIDES = [
    "abonnes", "factures", "consommations", "produits",
    "paiements", "fournisseurs", "compta", "mouvements_stock", "journal_log"
]

# --- Utilitaires ---
def connect_db():
    return sqlite3.connect(DB_PATH)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_action(utilisateur_id, action, description, statut="succes"):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO journal_log (utilisateur_id, action, description, statut)
        VALUES (?, ?, ?, ?)
    """, (utilisateur_id, action, description, statut))
    conn.commit()
    conn.close()

def _valider_table_colonnes(table, colonnes):
    if table not in TABLES_VALIDES:
        raise ValueError(f"Table invalide: {table}")
    for col in colonnes:
        if not col.isidentifier():
            raise ValueError(f"Colonne invalide: {col}")

# --- Génération automatique de numéros ---
def generer_numero(table):
    _valider_table_colonnes(table, [])
    prefix = {"abonnes": "ABN", "factures": "FAC"}.get(table, "GEN")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    n = cur.fetchone()[0] + 1
    conn.close()
    if table == "factures":
        return f"{prefix}-{datetime.now().year}-{n:04d}"
    return f"{prefix}-{n:05d}"

# --- CRUD principal ---
def create(table, data, utilisateur_id=None):
    _valider_table_colonnes(table, data.keys())
    conn = connect_db()
    try:
        cur = conn.cursor()

        # numéros automatiques
        if table == "abonnes" and "numero_abonne" not in data:
            data["numero_abonne"] = generer_numero("abonnes")
        if table == "factures" and "numero_facture" not in data:
            data["numero_facture"] = generer_numero("factures")

        champs = ", ".join(data.keys())
        valeurs = tuple(data.values())
        placeholders = ", ".join(["?"] * len(data))

        cur.execute(f"INSERT INTO {table} ({champs}) VALUES ({placeholders})", valeurs)
        inserted_id = cur.lastrowid

        # Automatismes
        if table == "consommations":
            _maj_stock_apres_vente(conn, cur, data["produit_id"], data["quantite"], utilisateur_id)
        if table == "paiements":
            _maj_facture_et_compta(conn, cur, data["facture_id"], data["montant"], data["mode"], utilisateur_id)

        log_action(utilisateur_id, f"CREATE:{table}", f"Insertion dans {table} ID={inserted_id}")
        conn.commit()
        return inserted_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def read(table, conditions=None):
    _valider_table_colonnes(table, conditions.keys() if conditions else [])
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if conditions:
        clause = " AND ".join([f"{k}=?" for k in conditions.keys()])
        cur.execute(f"SELECT * FROM {table} WHERE {clause}", tuple(conditions.values()))
    else:
        cur.execute(f"SELECT * FROM {table}")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

def update(table, data, conditions, utilisateur_id=None):
    _valider_table_colonnes(table, list(data.keys()) + list(conditions.keys()))
    conn = connect_db()
    try:
        cur = conn.cursor()
        champs = ", ".join([f"{k}=?" for k in data.keys()])
        conds = " AND ".join([f"{k}=?" for k in conditions.keys()])
        cur.execute(f"UPDATE {table} SET {champs} WHERE {conds}",
                    tuple(data.values()) + tuple(conditions.values()))
        log_action(utilisateur_id, f"UPDATE:{table}", f"Mise à jour {conditions}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete(table, conditions, utilisateur_id=None):
    _valider_table_colonnes(table, list(conditions.keys()))
    conn = connect_db()
    try:
        cur = conn.cursor()
        conds = " AND ".join([f"{k}=?" for k in conditions.keys()])
        cur.execute(f"DELETE FROM {table} WHERE {conds}", tuple(conditions.values()))
        log_action(utilisateur_id, f"DELETE:{table}", f"Suppression {conditions}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Automatismes internes ---
def _maj_stock_apres_vente(conn, cur, produit_id, quantite, utilisateur_id):
    cur.execute("SELECT stock, nom FROM produits WHERE id=?", (produit_id,))
    res = cur.fetchone()
    if not res:
        return
    stock_actuel, nom = res
    nouveau_stock = max(stock_actuel - quantite, 0)
    cur.execute("UPDATE produits SET stock=? WHERE id=?", (nouveau_stock, produit_id))
    cur.execute("""
        INSERT INTO mouvements_stock (produit_id, type_mouvement, quantite, motif, utilisateur_id)
        VALUES (?, 'SORTIE', ?, 'Vente', ?)
    """, (produit_id, quantite, utilisateur_id))
    log_action(utilisateur_id, "STOCK", f"Sortie de {quantite} unités de {nom} (reste {nouveau_stock})")

def _maj_facture_et_compta(conn, cur, facture_id, montant, mode, utilisateur_id):
    cur.execute("UPDATE factures SET statut='payee' WHERE id=?", (facture_id,))
    log_action(utilisateur_id, "PAIEMENT", f"Facture {facture_id} réglée ({montant} {mode})")
