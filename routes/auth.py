from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from flask import render_template

auth_bp = Blueprint("auth", __name__)

# Créer un utilisateur (inscription)
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Champs manquants"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Nom d'utilisateur déjà pris"}), 409

    new_user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Utilisateur créé avec succès"}), 201


# Connexion
@auth_bp.route("/login", methods=["POST"])
def login_api():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Champs manquants"}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session["user_id"] = user.id
        return jsonify({"message": "Connexion réussie", "user_id": user.id}), 200

    return jsonify({"message": "Identifiants invalides"}), 401


@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")



# Vérifier session utilisateur
@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Non connecté"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Utilisateur introuvable"}), 404

    return jsonify({"id": user.id, "username": user.username}), 200


# Déconnexion
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Déconnexion réussie"}), 200


    abort(500)