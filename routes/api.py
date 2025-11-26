from flask import Blueprint, request, jsonify
from models import db, User

api_bp = Blueprint('api', __name__)

# --- Vérifier un token ---
@api_bp.route('/auth', methods=['POST'])
def api_auth():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({"success": False, "message": "Identifiants invalides"}), 401

    return jsonify({"success": True, "user": {"id": user.id, "username": user.username}})


# --- Exemple: Liste des abonnés ---
@api_bp.route('/abonnes', methods=['GET'])
def get_abonnes():
    abonnes = [
        {"id": 1, "nom": "Dupont", "adresse": "Paris"},
        {"id": 2, "nom": "Traoré", "adresse": "Ouagadougou"},
    ]
    return jsonify(abonnes)


# --- Exemple: Ajouter un abonné ---
@api_bp.route('/abonnes', methods=['POST'])
def add_abonne():
    data = request.get_json()
    # En base : créer et commit
    return jsonify({"message": "Abonné ajouté", "data": data}), 201


