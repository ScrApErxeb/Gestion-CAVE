# core/produits.py
from datetime import datetime
from core.crud import create, read, update, log_action

# --- Créer un produit ---
def creer_produit(nom, categorie, prix_achat, prix_vente, fournisseur_id=None, utilisateur_id=None):
    data = {
        "nom": nom,
        "categorie": categorie,
        "prix_achat": prix_achat,
        "prix_vente": prix_vente,
        "stock": 0,
        "fournisseur_id": fournisseur_id
    }
    produit_id = create("produits", data, utilisateur_id)
    log_action(utilisateur_id, "PRODUIT_CREATE", f"Produit {nom} créé ({categorie})")
    return produit_id

# --- Modifier un produit ---
def modifier_produit(produit_id, nom=None, categorie=None, prix_achat=None, prix_vente=None, fournisseur_id=None, utilisateur_id=None):
    data = {}
    if nom: data["nom"] = nom
    if categorie: data["categorie"] = categorie
    if prix_achat is not None: data["prix_achat"] = prix_achat
    if prix_vente is not None: data["prix_vente"] = prix_vente
    if fournisseur_id: data["fournisseur_id"] = fournisseur_id
    if not data: return
    update("produits", data, {"id": produit_id})
    log_action(utilisateur_id, "PRODUIT_UPDATE", f"Produit {produit_id} mis à jour")

# --- Lister tous les produits ---
def lister_produits():
    return read("produits")

# --- Consulter le stock d’un produit ---
def stock_produit(produit_id):
    produits = read("produits", {"id": produit_id})
    return produits[0]["stock"] if produits else 0

# --- Mouvement de stock interne ---
def _mouvement_stock(produit_id, type_mouvement, quantite, reference="", utilisateur_id=None):
    """Modifie le stock et garde une trace dans journal_log"""
    produits = read("produits", {"id": produit_id})
    if not produits:
        return
    produit = produits[0]
    stock_actuel = produit["stock"]

    if type_mouvement == "ENTREE":
        nouveau_stock = stock_actuel + quantite
    elif type_mouvement == "SORTIE":
        nouveau_stock = max(0, stock_actuel - quantite)
    else:
        return

    update("produits", {"stock": nouveau_stock}, {"id": produit_id})
    log_action(utilisateur_id, "STOCK_MVT", f"{type_mouvement} {quantite} unités (prod {produit_id}) {reference}")

# --- Entrée initiale de stock (inventaire de départ) ---
def entree_initiale(produit_id, quantite, utilisateur_id=None):
    _mouvement_stock(produit_id, "ENTREE", quantite, "Entrée initiale", utilisateur_id)
