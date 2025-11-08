# core/ventes.py
from datetime import datetime
from core.crud import create, read, update, log_action
from core.produits import _mouvement_stock
from core.compta import enregistrer_recette

# --- Enregistrer une consommation (vente directe ou sur compte abonné) ---
def enregistrer_consommation(abonne_id, produit_id, quantite, utilisateur_id=None):
    # 1. Créer une ligne consommation
    data = {
        "abonne_id": abonne_id,
        "produit_id": produit_id,
        "quantite": quantite
    }
    conso_id = create("consommations", data, utilisateur_id)

    # 2. Décrémenter le stock
    _mouvement_stock(produit_id, "SORTIE", quantite, "Vente", utilisateur_id)

    # 3. Créer ou mettre à jour la facture courante de l’abonné
    facture_id = _facture_active(abonne_id)
    if not facture_id:
        facture_id = creer_facture(abonne_id, utilisateur_id)

    _ajouter_produit_facture(facture_id, produit_id, quantite)

    log_action(utilisateur_id, "VENTE", f"Abonné {abonne_id} a consommé {quantite} unité(s) du produit {produit_id}")
    return conso_id

# --- Création d’une facture ---
def creer_facture(abonne_id, utilisateur_id=None):
    numero = datetime.now().strftime("FAC-%Y-%m%d-%H%M%S")
    data = {
        "numero_facture": numero,
        "abonne_id": abonne_id,
        "montant_total": 0.0,
        "statut": "en_attente"
    }
    facture_id = create("factures", data, utilisateur_id)
    log_action(utilisateur_id, "FACTURE_CREATE", f"Facture {numero} créée pour abonné {abonne_id}")
    return facture_id

# --- Ajouter un produit à une facture ---
def _ajouter_produit_facture(facture_id, produit_id, quantite):
    """Calcule le total et met à jour la facture."""
    produits = read("produits", {"id": produit_id})
    if not produits:
        return
    produit = produits[0]
    montant = produit["prix_vente"] * quantite

    facture = read("factures", {"id": facture_id})[0]
    nouveau_total = facture["montant_total"] + montant
    update("factures", {"montant_total": nouveau_total}, {"id": facture_id})

# --- Paiement d’une facture ---
def payer_facture(facture_id, montant, mode, utilisateur_id=None):
    data = {
        "facture_id": facture_id,
        "montant": montant,
        "mode": mode
    }
    paiement_id = create("paiements", data, utilisateur_id)

    # Mise à jour compta (recette)
    enregistrer_recette(montant, f"FAC#{facture_id}", f"Paiement via {mode}")

    # Passage de la facture à payée
    update("factures", {"statut": "payee"}, {"id": facture_id})
    log_action(utilisateur_id, "FACTURE_PAYEE", f"Facture {facture_id} réglée ({montant} {mode})")

    return paiement_id

# --- Vérifie s’il existe une facture non payée pour l’abonné ---
def _facture_active(abonne_id):
    factures = read("factures", {"abonne_id": abonne_id, "statut": "en_attente"})
    return factures[0]["id"] if factures else None
