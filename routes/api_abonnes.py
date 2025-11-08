from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Abonne
from datetime import datetime

abonnes_bp = Blueprint('abonnes', __name__)

@abonnes_bp.route('/abonnes', methods=['GET'])
@login_required
def get_abonnes():
    """Récupérer tous les abonnés"""
    try:
        recherche = request.args.get('recherche', '')
        actif = request.args.get('actif', 'true').lower() == 'true'
        
        query = Abonne.query
        
        if actif:
            query = query.filter_by(actif=True)
        
        if recherche:
            recherche_pattern = f'%{recherche}%'
            query = query.filter(
                db.or_(
                    Abonne.numero_abonne.like(recherche_pattern),
                    Abonne.nom.like(recherche_pattern),
                    Abonne.prenom.like(recherche_pattern),
                    Abonne.telephone.like(recherche_pattern)
                )
            )
        
        abonnes = query.order_by(Abonne.nom).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': a.id,
                'numero_abonne': a.numero_abonne,
                'nom': a.nom,
                'prenom': a.prenom,
                'nom_complet': a.nom_complet,
                'telephone': a.telephone,
                'email': a.email,
                'adresse': a.adresse,
                'date_inscription': a.date_inscription.isoformat(),
                'actif': a.actif,
                'limite_credit': a.limite_credit,
                'solde_du': a.solde_du
            } for a in abonnes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@abonnes_bp.route('/abonnes/<int:id>', methods=['GET'])
@login_required
def get_abonne(id):
    """Récupérer un abonné spécifique"""
    try:
        abonne = Abonne.query.get_or_404(id)
        
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
                'date_inscription': abonne.date_inscription.isoformat(),
                'actif': abonne.actif,
                'limite_credit': abonne.limite_credit,
                'solde_du': abonne.solde_du,
                'factures': [{
                    'id': f.id,
                    'numero_facture': f.numero_facture,
                    'montant_ttc': f.montant_ttc,
                    'statut': f.statut,
                    'date_emission': f.date_emission.isoformat()
                } for f in abonne.factures]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@abonnes_bp.route('/abonnes', methods=['POST'])
@login_required
def create_abonne():
    """Créer un nouvel abonné"""
    if not current_user.has_permission('abonnes'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('nom') or not data.get('telephone'):
            return jsonify({'success': False, 'error': 'Nom et téléphone obligatoires'}), 400
        
        # Vérifier si le numéro d'abonné existe déjà
        if data.get('numero_abonne'):
            existe = Abonne.query.filter_by(numero_abonne=data['numero_abonne']).first()
            if existe:
                return jsonify({'success': False, 'error': 'Numéro d\'abonné déjà utilisé'}), 400
        else:
            # Générer un numéro automatique
            dernier = Abonne.query.order_by(Abonne.id.desc()).first()
            prochain_numero = (dernier.id + 1) if dernier else 1
            data['numero_abonne'] = f'ABN{prochain_numero:05d}'
        
        abonne = Abonne(
            numero_abonne=data['numero_abonne'],
            nom=data['nom'],
            prenom=data.get('prenom', ''),
            telephone=data['telephone'],
            email=data.get('email', ''),
            adresse=data.get('adresse', ''),
            limite_credit=data.get('limite_credit', 0)
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
        return jsonify({'success': False, 'error': str(e)}), 500

@abonnes_bp.route('/abonnes/<int:id>', methods=['PUT'])
@login_required
def update_abonne(id):
    """Mettre à jour un abonné"""
    if not current_user.has_permission('abonnes'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        abonne = Abonne.query.get_or_404(id)
        data = request.get_json()
        
        # Mise à jour des champs
        if 'nom' in data:
            abonne.nom = data['nom']
        if 'prenom' in data:
            abonne.prenom = data['prenom']
        if 'telephone' in data:
            abonne.telephone = data['telephone']
        if 'email' in data:
            abonne.email = data['email']
        if 'adresse' in data:
            abonne.adresse = data['adresse']
        if 'limite_credit' in data:
            abonne.limite_credit = data['limite_credit']
        if 'actif' in data:
            abonne.actif = data['actif']
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@abonnes_bp.route('/abonnes/<int:id>', methods=['DELETE'])
@login_required
def delete_abonne(id):
    """Désactiver un abonné (soft delete)"""
    if not current_user.has_permission('abonnes'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        abonne = Abonne.query.get_or_404(id)
        
        # Vérifier si l'abonné a des factures impayées
        factures_impayees = [f for f in abonne.factures if f.statut != 'payee']
        if factures_impayees:
            return jsonify({
                'success': False,
                'error': 'Impossible de désactiver un abonné avec des factures impayées'
            }), 400
        
        abonne.actif = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Abonné désactivé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@abonnes_bp.route('/abonnes/<int:id>/historique', methods=['GET'])
@login_required
def get_historique_abonne(id):
    """Récupérer l'historique des consommations d'un abonné"""
    try:
        abonne = Abonne.query.get_or_404(id)
        
        consommations = [{
            'id': c.id,
            'date': c.date.isoformat(),
            'produit': c.produit.nom,
            'quantite': c.quantite,
            'prix_unitaire': c.prix_unitaire,
            'montant_total': c.montant_total,
            'facture_id': c.facture_id
        } for c in abonne.consommations]
        
        return jsonify({
            'success': True,
            'data': consommations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500