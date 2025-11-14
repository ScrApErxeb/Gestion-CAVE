from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Facture, Consommation, Abonne
from datetime import datetime, timedelta

factures_bp = Blueprint('factures', __name__)

@factures_bp.route('/factures', methods=['GET'])
@login_required
def get_factures():
    """Récupérer toutes les factures"""
    try:
        statut = request.args.get('statut', '')
        abonne_id = request.args.get('abonne_id', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')
        
        query = Facture.query
        
        if statut:
            query = query.filter_by(statut=statut)
        
        if abonne_id:
            query = query.filter_by(abonne_id=int(abonne_id))
        
        if date_debut:
            date_d = datetime.fromisoformat(date_debut)
            query = query.filter(Facture.date_emission >= date_d)
        
        if date_fin:
            date_f = datetime.fromisoformat(date_fin)
            query = query.filter(Facture.date_emission <= date_f)
        
        factures = query.order_by(Facture.date_emission.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': f.id,
                'numero_facture': f.numero_facture,
                'abonne': f.abonne.nom_complet,
                'abonne_id': f.abonne_id,
                'montant_ht': f.montant_ht,
                'montant_tva': f.montant_tva,
                'montant_ttc': f.montant_ttc,
                'statut': f.statut,
                'date_emission': f.date_emission.isoformat(),
                'date_echeance': f.date_echeance.isoformat() if f.date_echeance else None,
                'montant_paye': f.montant_paye,
                'reste_a_payer': f.reste_a_payer
            } for f in factures]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@factures_bp.route('/factures/<int:id>', methods=['GET'])
@login_required
def get_facture(id):
    """Récupérer une facture spécifique avec ses détails"""
    try:
        facture = Facture.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id': facture.id,
                'numero_facture': facture.numero_facture,
                'abonne': {
                    'id': facture.abonne.id,
                    'numero_abonne': facture.abonne.numero_abonne,
                    'nom_complet': facture.abonne.nom_complet,
                    'telephone': facture.abonne.telephone
                },
                'montant_ht': facture.montant_ht,
                'taux_tva': facture.taux_tva,
                'montant_tva': facture.montant_tva,
                'montant_ttc': facture.montant_ttc,
                'statut': facture.statut,
                'date_emission': facture.date_emission.isoformat(),
                'date_echeance': facture.date_echeance.isoformat() if facture.date_echeance else None,
                'createur': facture.createur.nom_complet if facture.createur else None,
                'note': facture.note,
                'consommations': [{
                    'id': c.id,
                    'produit': c.produit.nom,
                    'quantite': c.quantite,
                    'prix_unitaire': c.prix_unitaire,
                    'montant_total': c.montant_total
                } for c in facture.consommations],
                'paiements': [{
                    'id': p.id,
                    'montant': p.montant,
                    'mode_paiement': p.mode_paiement,
                    'date_paiement': p.date_paiement.isoformat(),
                    'reference': p.reference
                } for p in facture.paiements],
                'montant_paye': facture.montant_paye,
                'reste_a_payer': facture.reste_a_payer
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@factures_bp.route('/factures', methods=['POST'])
@login_required
def create_facture():
    """Créer une nouvelle facture à partir des consommations"""
    if not current_user.has_permission('factures'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('abonne_id'):
            return jsonify({'success': False, 'error': 'Abonné obligatoire'}), 400
        
        if not data.get('consommation_ids') or len(data['consommation_ids']) == 0:
            return jsonify({'success': False, 'error': 'Au moins une consommation requise'}), 400
        
        abonne = Abonne.query.get_or_404(data['abonne_id'])
        
        # Générer numéro de facture
        date_str = datetime.now().strftime('%Y%m')
        dernier = Facture.query.filter(
            Facture.numero_facture.like(f'FAC-{date_str}-%')
        ).order_by(Facture.id.desc()).first()
        
        if dernier:
            dernier_num = int(dernier.numero_facture.split('-')[-1])
            nouveau_num = dernier_num + 1
        else:
            nouveau_num = 1
        
        numero_facture = f'FAC-{date_str}-{nouveau_num:04d}'
        
        # Créer la facture
        facture = Facture(
            numero_facture=numero_facture,
            abonne_id=data['abonne_id'],
            date_echeance=datetime.fromisoformat(data['date_echeance']) if data.get('date_echeance') else datetime.now() + timedelta(days=30),
            created_by_id=current_user.id,
            note=data.get('note', '')
        )
        
        db.session.add(facture)
        db.session.flush()  # Pour obtenir l'ID de la facture
        
        # Associer les consommations
        for conso_id in data['consommation_ids']:
            conso = Consommation.query.get(conso_id)
            if conso and conso.facture_id is None:
                conso.facture_id = facture.id
        
        # Calculer les montants
        facture.calculer_montants()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Facture créée avec succès',
            'data': {
                'id': facture.id,
                'numero_facture': facture.numero_facture,
                'montant_ttc': facture.montant_ttc
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@factures_bp.route('/factures/<int:id>', methods=['PUT'])
@login_required
def update_facture(id):
    """Mettre à jour une facture"""
    if not current_user.has_permission('factures'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        facture = Facture.query.get_or_404(id)
        data = request.get_json()
        
        # Empêcher la modification d'une facture payée
        if facture.statut == 'payee' and not current_user.role == 'admin':
            return jsonify({'success': False, 'error': 'Impossible de modifier une facture payée'}), 400
        
        if 'date_echeance' in data:
            facture.date_echeance = datetime.fromisoformat(data['date_echeance'])
        if 'note' in data:
            facture.note = data['note']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Facture mise à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@factures_bp.route('/factures/<int:id>', methods=['DELETE'])
@login_required
def delete_facture(id):
    """Supprimer une facture (admin uniquement)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        facture = Facture.query.get_or_404(id)
        
        # Empêcher la suppression d'une facture avec paiements
        if facture.paiements:
            return jsonify({'success': False, 'error': 'Impossible de supprimer une facture avec des paiements'}), 400
        
        # Détacher les consommations
        for conso in facture.consommations:
            conso.facture_id = None
        
        db.session.delete(facture)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Facture supprimée avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@factures_bp.route('/factures/abonne/<int:abonne_id>/non-facturees', methods=['GET'])
@login_required
def get_consommations_non_facturees(abonne_id):
    """Récupérer les consommations non facturées d'un abonné"""
    try:
        consommations = Consommation.query.filter_by(
            abonne_id=abonne_id,
            facture_id=None
        ).order_by(Consommation.date.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': c.id,
                'date': c.date.isoformat(),
                'produit': c.produit.nom,
                'quantite': c.quantite,
                'prix_unitaire': c.prix_unitaire,
                'montant_total': c.montant_total
            } for c in consommations]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500