# core/compta.py
from datetime import datetime
from core.crud import create, read, update, log_action

# --- Enregistrer une recette (entrée d’argent) ---
def enregistrer_recette(montant, reference, description="", utilisateur_id=None):
    data = {
        "date_operation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type_operation": "RECETTE",
        "montant": montant,
        "reference": reference,
        "description": description
    }
    create("comptabilite", data, utilisateur_id)
    log_action(utilisateur_id, "RECETTE", f"{montant} enregistré ({reference})")

# --- Enregistrer une dépense (sortie d’argent) ---
def enregistrer_depense(montant, reference, description="", utilisateur_id=None):
    data = {
        "date_operation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type_operation": "DEPENSE",
        "montant": montant,
        "reference": reference,
        "description": description
    }
    create("comptabilite", data, utilisateur_id)
    log_action(utilisateur_id, "DEPENSE", f"{montant} débité ({reference})")

# --- Calculer le solde actuel ---
def solde_actuel():
    lignes = read("comptabilite")
    total_recette = sum(l["montant"] for l in lignes if l["type_operation"] == "RECETTE")
    total_depense = sum(l["montant"] for l in lignes if l["type_operation"] == "DEPENSE")
    return total_recette - total_depense

# --- Générer un rapport comptable sommaire ---
def rapport_comptable():
    lignes = read("comptabilite")
    total_recette = sum(l["montant"] for l in lignes if l["type_operation"] == "RECETTE")
    total_depense = sum(l["montant"] for l in lignes if l["type_operation"] == "DEPENSE")
    solde = total_recette - total_depense
    return {
        "total_recette": total_recette,
        "total_depense": total_depense,
        "solde": solde,
        "dernieres_ops": lignes[-10:] if lignes else []
    }
