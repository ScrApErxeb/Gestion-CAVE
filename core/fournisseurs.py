# core/fournisseurs.py
from datetime import datetime
from core.crud import create, read, update, log_action
from core.produits import _mouvement_stock

# --- Créer un fournisseur ---
def creer_fournisseur(nom, contact=None, utilisateur_id=None):
    data = {
        "nom": nom,
        "contact": contact
    }
    fournisseur_id = create("fournisseurs", data, utilisateur_id)
    log_action(utilisateur_id, "FOURNISSEUR_CREATE", f"Nouveau fournisseur {nom}")
    return fournisseur_id

# --- Lister les fournisseurs ---
def lister_fournisseurs():
    return read("fournisseurs")

# --- Modifier un fournisseur ---
def modifier_fournisseur(fournisseur_id, nom=None, contact=None, utilisateur_id=None):
    data = {}
    if nom: data["nom"] = nom
    if contact: data["contact"] = contact
    if not data: return
    update("fournisseurs", data, {"id": fournisseur_id})
    log_action(utilisateur_id, "FOURNISSEUR_UPDATE", f"Fournisseur {fournisseur_id} mis à jour")

# --- Enregistrer une livraison de produits ---
def enregistrer_livraison(fournisseur_id, produit_id, quantite, prix_achat_unitaire, utilisateur_id=None):
    """Ajoute du stock + mouvement + enregistrement achat"""
    total = quantite * prix_achat_unitaire
    data = {
        "fournisseur_id": fournisseur_id,
        "produit_id": produit_id,
        "quantite": quantite,
        "prix_achat": prix_achat_unitaire,
        "date_livraison": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    create("achats", data, utilisateur_id)

    # mouvement de stock (entrée)
    _mouvement_stock(produit_id, "ENTREE", quantite, f"Livraison fournisseur {fournisseur_id}", utilisateur_id)

    # log
    log_action(utilisateur_id, "LIVRAISON", f"Produit {produit_id}: +{quantite} (four. {fournisseur_id})")

    return total
