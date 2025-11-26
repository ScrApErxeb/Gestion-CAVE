# routes/api_abonnes.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Abonne, Facture
from datetime import datetime
from sqlalchemy import or_, func

abonnes_bp = Blueprint('abonnes', __name__)

@abonnes_bp.route('/abonnes', methods=['GET'])
@login_required
def get_abonnes():
    """Récupérer tous les abonnés"""
    try:
        recherche = request.args.get('recherche', '').strip()
        actif = request.args.get('actif', 'true').lower() == 'true'

        query = Abonne.query
        if actif:
            query = query.filter_by(actif=True)

        if recherche:
            pattern = f"%{recherche}%"
            query = query.filter(
                or_(
                    Abonne.numero_abonne.like(pattern),
                    Abonne.nom.like(pattern),
                    Abonne.prenom.like(pattern),
                    Abonne.telephone.like(pattern)
                )
            )

        abonnes = query.order_by(Abonne.nom).all()

        data = []
        for a in abonnes:
            data.append({
                'id': a.id,
                'numero_abonne': a.numero_abonne,
                'nom': a.nom,
                'prenom': a.prenom,
                'nom_complet': a.nom_complet,
                'telephone': a.telephone,
                'conso_totale': a.conso_totale,  # ⚡ nouvelle info
                'solde_du': a.solde_du
            })

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        # Log serveur à faire ici
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500


@abonnes_bp.route('/abonnes/<int:id>', methods=['GET'])
@login_required
def get_abonne(id):
    """Récupérer un abonné spécifique"""
    try:
        abonne = Abonne.query.get_or_404(id)
        factures_data = []
        for f in abonne.factures:
            factures_data.append({
                'id': f.id,
                'numero_facture': f.numero_facture,
                'montant_ttc': f.montant_ttc,
                'statut': f.statut,
                'date_emission': f.date_emission.isoformat() if f.date_emission else None
            })

        return jsonify({
            'success': True,
            'data': {
                'id': abonne.id,
                'numero_abonne': abonne.numero_abonne,
                'nom': abonne.nom,
                'prenom': abonne.prenom,
                'nom_complet': abonne.nom_complet,
                'telephone': abonne.telephone,
                'email': abonne.email,
                'adresse': abonne.adresse,
                'date_inscription': abonne.date_inscription.isoformat() if abonne.date_inscription else None,
                'actif': abonne.actif,
                'limite_credit': abonne.limite_credit,
                'solde_du': abonne.solde_du,
                'factures': factures_data
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500


@abonnes_bp.route('/abonnes', methods=['POST'])
@login_required
def create_abonne():
    """Créer un nouvel abonné"""
    if not current_user.has_permission('abonnes'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        data = request.get_json()
        nom = data.get('nom', '').strip()
        telephone = data.get('telephone', '').strip()

        if not nom or not telephone:
            return jsonify({'success': False, 'error': 'Nom et téléphone obligatoires'}), 400

        # Numéro abonné unique
        numero = data.get('numero_abonne')
        if numero:
            if Abonne.query.filter_by(numero_abonne=numero).first():
                return jsonify({'success': False, 'error': 'Numéro d\'abonné déjà utilisé'}), 400
        else:
            # Générer numéro unique basé sur max(id)
            max_id = db.session.query(func.max(Abonne.id)).scalar() or 0
            numero = f'ABN{max_id + 1:05d}'

        abonne = Abonne(
            numero_abonne=numero,
            nom=nom,
            prenom=data.get('prenom', '').strip(),
            telephone=telephone,
            email=data.get('email', '').strip(),
            adresse=data.get('adresse', '').strip(),
            limite_credit=data.get('limite_credit', 0),
            actif=True,
            date_inscription=datetime.utcnow()
        )

        db.session.add(abonne)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Abonné créé avec succès',
            'data': {
                'id': abonne.id,
                'numero_abonne': abonne.numero_abonne,
                'nom_complet': abonne.nom_complet
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500


@abonnes_bp.route('/abonnes/<int:id>', methods=['PUT'])
@login_required
def update_abonne(id):
    """Mettre à jour un abonné"""
    if not current_user.has_permission('abonnes'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        abonne = Abonne.query.get_or_404(id)
        data = request.get_json()

        for field in ['nom', 'prenom', 'telephone', 'email', 'adresse', 'limite_credit', 'actif']:
            if field in data:
                setattr(abonne, field, data[field])

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Abonné mis à jour avec succès',
            'data': {
                'id': abonne.id,
                'numero_abonne': abonne.numero_abonne,
                'nom_complet': abonne.nom_complet
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500


@abonnes_bp.route('/abonnes/<int:id>', methods=['DELETE'])
@login_required
def delete_abonne(id):
    """Désactiver un abonné (soft delete)"""
    if not current_user.has_permission('abonnes'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        abonne = Abonne.query.get_or_404(id)
        # Filtrage SQL pour factures impayées
        impayees = Facture.query.filter_by(abonne_id=id).filter(Facture.statut != 'payee').count()
        if impayees > 0:
            return jsonify({'success': False, 'error': 'Abonné a des factures impayées'}), 400

        abonne.actif = False
        db.session.commit()

        return jsonify({'success': True, 'message': 'Abonné désactivé avec succès'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500


@abonnes_bp.route('/abonnes/<int:id>/historique', methods=['GET'])
@login_required
def get_historique_abonne(id):
    """Récupérer l'historique des consommations d'un abonné"""
    try:
        abonne = Abonne.query.get_or_404(id)

        data = []
        for c in abonne.consommations:
            data.append({
                'id': c.id,
                'date': c.date.isoformat() if c.date else None,
                'produit': c.produit.nom,
                'quantite': c.quantite,
                'prix_unitaire': c.prix_unitaire,
                'montant_total': c.montant_total,
                'facture_id': c.facture_id
            })

        return jsonify({'success': True, 'data': data})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500
