from flask import Blueprint, jsonify, request
from models import db, Abonne

api_abonnes = Blueprint("api_abonnes", __name__)

@api_abonnes.route("/api/abonnes", methods=["GET"])
def get_abonnes():
    abonnes = Abonne.query.all()
    return jsonify([a.to_dict() for a in abonnes])

@api_abonnes.route("/api/abonnes", methods=["POST"])
def add_abonne():
    data = request.json
    abonne = Abonne(
        numero_abonne=data.get("numero_abonne"),
        nom=data.get("nom"),
        telephone=data.get("telephone")
    )
    db.session.add(abonne)
    db.session.commit()
    return jsonify(abonne.to_dict()), 201

@api_abonnes.route("/api/abonnes/<int:id>", methods=["DELETE"])
def delete_abonne(id):
    abonne = Abonne.query.get_or_404(id)
    db.session.delete(abonne)
    db.session.commit()
    return jsonify({"message": "Abonné supprimé"})
