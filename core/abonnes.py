# core/abonnes.py
from core.crud import create, read, update, log_action
from core.ventes import _facture_active

# --- Créer un nouvel abonné ---
def creer_abonne(nom, telephone=None, utilisateur_id=None):
    data = {
        "nom": nom,
        "telephone": telephone
    }
    abonne_id = create("abonnes", data, utilisateur_id)
    log_action(utilisateur_id, "ABONNE_CREATE", f"Nouvel abonné {nom}")
    return abonne_id

# --- Rechercher un abonné par nom ou numéro ---
def rechercher_abonne(critere):
    if critere.isdigit():
        resultats = read("abonnes", {"numero_abonne": critere})
    else:
        resultats = [a for a in read("abonnes") if critere.lower() in a["nom"].lower()]
    return resultats

# --- Mettre à jour les infos d’un abonné ---
def modifier_abonne(abonne_id, nom=None, telephone=None, utilisateur_id=None):
    data = {}
    if nom: data["nom"] = nom
    if telephone: data["telephone"] = telephone
    if not data: return
    update("abonnes", data, {"id": abonne_id})
    log_action(utilisateur_id, "ABONNE_UPDATE", f"Abonné {abonne_id} mis à jour")

# --- Historique de consommation ---
def historique_consommation(abonne_id):
    consommations = read("consommations", {"abonne_id": abonne_id})
    return consommations

# --- Facture courante (non payée) ---
def facture_en_cours(abonne_id):
    fid = _facture_active(abonne_id)
    return fid
