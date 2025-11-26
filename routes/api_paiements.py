from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Paiement, Facture
from datetime import datetime

paiements_bp = Blueprint('paiements', __name__)

@paiements_bp.route('/paiements', methods=['GET'])
@login_required
def get_paiements():
    """Récupérer tous les paiements"""
    try:
        facture_id = request.args.get('facture_id', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')
        mode_paiement = request.args.get('mode_paiement', '')
        
        query = Paiement.query
        
        if facture_id:
            query = query.filter_by(facture_id=int(facture_id))
        
        if mode_paiement:
            query = query.filter_by(mode_paiement=mode_paiement)
        
        if date_debut:
            date_d = datetime.fromisoformat(date_debut)
            query = query.filter(Paiement.date_paiement >= date_d)
        
        if date_fin:
            date_f = datetime.fromisoformat(date_fin)
            query = query.filter(Paiement.date_paiement <= date_f)
        
        paiements = query.order_by(Paiement.date_paiement.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': p.id,
                'facture_numero': p.facture.numero_facture,
                'facture_id': p.facture_id,
                'abonne': p.facture.abonne.nom_complet,
                'montant': p.montant,
                'mode_paiement': p.mode_paiement,
                'reference': p.reference,
                'date_paiement': p.date_paiement.isoformat(),
                'recu_par': p.recu_par,
                'note': p.note
            } for p in paiements]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@paiements_bp.route('/paiements/<int:id>', methods=['GET'])
@login_required
def get_paiement(id):
    """Récupérer un paiement spécifique"""
    try:
        paiement = Paiement.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id': paiement.id,
                'facture': {
                    'id': paiement.facture.id,
                    'numero_facture': paiement.facture.numero_facture,
                    'abonne': paiement.facture.abonne.nom_complet,
                    'montant_ttc': paiement.facture.montant_ttc,
                    'reste_a_payer': paiement.facture.reste_a_payer
                },
                'montant': paiement.montant,
                'mode_paiement': paiement.mode_paiement,
                'reference': paiement.reference,
                'date_paiement': paiement.date_paiement.isoformat(),
                'recu_par': paiement.recu_par,
                'note': paiement.note
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@paiements_bp.route('/paiements', methods=['POST'])
@login_required
def create_paiement():
    """Enregistrer un nouveau paiement"""
    if not current_user.has_permission('paiements'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('facture_id') or not data.get('montant') or not data.get('mode_paiement'):
            return jsonify({'success': False, 'error': 'Facture, montant et mode de paiement obligatoires'}), 400
        
        facture = Facture.query.get_or_404(data['facture_id'])
        
        # Vérifier que le montant ne dépasse pas le reste à payer
        montant = float(data['montant'])
        if montant > facture.reste_a_payer:
            return jsonify({
                'success': False,
                'error': f'Montant supérieur au reste à payer ({facture.reste_a_payer} FCFA)'
            }), 400
        
        # Créer le paiement
        paiement = Paiement(
            facture_id=data['facture_id'],
            montant=montant,
            mode_paiement=data['mode_paiement'],
            reference=data.get('reference', ''),
            date_paiement=datetime.fromisoformat(data['date_paiement']) if data.get('date_paiement') else datetime.now(),
            recu_par=data.get('recu_par', current_user.nom_complet or current_user.username),
            note=data.get('note', '')
        )
        
        db.session.add(paiement)  
        #
        
        # Mettre à jour le statut de la facture
        facture.mettre_a_jour_statut()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paiement enregistré avec succès',
            'data': {
                'id': paiement.id,
                'montant': paiement.montant,
                'facture_statut': facture.statut,
                'reste_a_payer': facture.reste_a_payer
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@paiements_bp.route('/paiements/<int:id>', methods=['PUT'])
@login_required
def update_paiement(id):
    """Mettre à jour un paiement (admin uniquement)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        paiement = Paiement.query.get_or_404(id)
        data = request.get_json()
        
        if 'montant' in data:
            ancien_montant = paiement.montant
            nouveau_montant = float(data['montant'])
            
            # Vérifier que le nouveau montant est valide
            facture = paiement.facture
            reste_disponible = facture.reste_a_payer + ancien_montant
            
            if nouveau_montant > reste_disponible:
                return jsonify({
                    'success': False,
                    'error': f'Montant supérieur au reste à payer ({reste_disponible} FCFA)'
                }), 400
            
            paiement.montant = nouveau_montant
        
        if 'mode_paiement' in data:
            paiement.mode_paiement = data['mode_paiement']
        if 'reference' in data:
            paiement.reference = data['reference']
        if 'note' in data:
            paiement.note = data['note']
        
        # Mettre à jour le statut de la facture
        paiement.facture.mettre_a_jour_statut()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paiement mis à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@paiements_bp.route('/paiements/<int:id>', methods=['DELETE'])
@login_required
def delete_paiement(id):
    """Supprimer un paiement (admin uniquement)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        paiement = Paiement.query.get_or_404(id)
        facture = paiement.facture
        
        db.session.delete(paiement)
        
        # Mettre à jour le statut de la facture
        facture.mettre_a_jour_statut()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paiement supprimé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@paiements_bp.route('/paiements/modes', methods=['GET'])
@login_required
def get_modes_paiement():
    """Récupérer la liste des modes de paiement disponibles"""
    modes = [
        {'value': 'especes', 'label': 'Espèces'},
        {'value': 'mobile_money', 'label': 'Mobile Money'},
        {'value': 'cheque', 'label': 'Chèque'},
        {'value': 'carte', 'label': 'Carte bancaire'},
        {'value': 'virement', 'label': 'Virement bancaire'}
    ]
    
    return jsonify({
        'success': True,
        'data': modes
    })

@paiements_bp.route('/paiements/statistiques', methods=['GET'])
@login_required
def get_statistiques_paiements():
    """Récupérer les statistiques des paiements"""
    try:
        date_debut = request.args.get('date_debut')
        date_fin = request.args.get('date_fin')
        
        query = Paiement.query
        
        if date_debut:
            date_d = datetime.fromisoformat(date_debut)
            query = query.filter(Paiement.date_paiement >= date_d)
        
        if date_fin:
            date_f = datetime.fromisoformat(date_fin)
            query = query.filter(Paiement.date_paiement <= date_f)
        
        paiements = query.all()
        
        # Calcul par mode de paiement
        stats_par_mode = {}
        for p in paiements:
            if p.mode_paiement not in stats_par_mode:
                stats_par_mode[p.mode_paiement] = {'count': 0, 'total': 0}
            stats_par_mode[p.mode_paiement]['count'] += 1
            stats_par_mode[p.mode_paiement]['total'] += p.montant
        
        total_general = sum(p.montant for p in paiements)
        
        return jsonify({
            'success': True,
            'data': {
                'total_paiements': len(paiements),
                'montant_total': total_general,
                'par_mode': stats_par_mode
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500