from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Consommation, Produit, Abonne, StockLog
from datetime import datetime

consommations_bp = Blueprint('consommations', __name__)

@consommations_bp.route('/consommations', methods=['GET'])
@login_required
def get_consommations():
    """Récupérer toutes les consommations"""
    try:
        abonne_id = request.args.get('abonne_id', '')
        produit_id = request.args.get('produit_id', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')
        facturees = request.args.get('facturees', '')
        
        query = Consommation.query
        
        if abonne_id:
            query = query.filter_by(abonne_id=int(abonne_id))
        
        if produit_id:
            query = query.filter_by(produit_id=int(produit_id))
        
        if date_debut:
            date_d = datetime.fromisoformat(date_debut)
            query = query.filter(Consommation.date >= date_d)
        
        if date_fin:
            date_f = datetime.fromisoformat(date_fin)
            query = query.filter(Consommation.date <= date_f)
        
        if facturees == 'true':
            query = query.filter(Consommation.facture_id.isnot(None))
        elif facturees == 'false':
            query = query.filter(Consommation.facture_id.is_(None))
        
        consommations = query.order_by(Consommation.date.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': c.id,
                'abonne': c.abonne.nom_complet,
                'abonne_id': c.abonne_id,
                'produit': c.produit.nom,
                'produit_id': c.produit_id,
                'quantite': c.quantite,
                'prix_unitaire': c.prix_unitaire,
                'montant_total': c.montant_total,
                'date': c.date.isoformat(),
                'facture_id': c.facture_id,
                'facture_numero': c.facture.numero_facture if c.facture else None,
                'note': c.note
            } for c in consommations]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@consommations_bp.route('/consommations/<int:id>', methods=['GET'])
@login_required
def get_consommation(id):
    """Récupérer une consommation spécifique"""
    try:
        consommation = Consommation.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id': consommation.id,
                'abonne': {
                    'id': consommation.abonne.id,
                    'numero_abonne': consommation.abonne.numero_abonne,
                    'nom_complet': consommation.abonne.nom_complet
                },
                'produit': {
                    'id': consommation.produit.id,
                    'nom': consommation.produit.nom,
                    'prix_vente': consommation.produit.prix_vente
                },
                'quantite': consommation.quantite,
                'prix_unitaire': consommation.prix_unitaire,
                'montant_total': consommation.montant_total,
                'date': consommation.date.isoformat(),
                'facture_id': consommation.facture_id,
                'note': consommation.note
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@consommations_bp.route('/consommations', methods=['POST'])
@login_required
def create_consommation():
    """Enregistrer une nouvelle consommation"""
    if not current_user.has_permission('consommations'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('abonne_id') or not data.get('produit_id') or not data.get('quantite'):
            return jsonify({'success': False, 'error': 'Abonné, produit et quantité obligatoires'}), 400
        
        abonne = Abonne.query.get_or_404(data['abonne_id'])
        produit = Produit.query.get_or_404(data['produit_id'])
        quantite = int(data['quantite'])
        
        # Vérifier le stock
        if produit.stock < quantite:
            return jsonify({
                'success': False,
                'error': f'Stock insuffisant (disponible: {produit.stock})'
            }), 400
        
        # Prix unitaire (prix actuel du produit ou prix personnalisé)
        prix_unitaire = float(data.get('prix_unitaire', produit.prix_vente))
        
        # Créer la consommation
        consommation = Consommation(
            abonne_id=data['abonne_id'],
            produit_id=data['produit_id'],
            quantite=quantite,
            prix_unitaire=prix_unitaire,
            montant_total=quantite * prix_unitaire,
            note=data.get('note', '')
        )
        
        # Mettre à jour le stock
        stock_avant = produit.stock
        produit.stock -= quantite
        
        # Enregistrer le mouvement de stock
        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='sortie',
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=f'Vente à {abonne.nom_complet}',
            reference=f'Consommation #{consommation.id}'
        )
        
        db.session.add(consommation)
        db.session.add(stock_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Consommation enregistrée avec succès',
            'data': {
                'id': consommation.id,
                'montant_total': consommation.montant_total,
                'stock_restant': produit.stock
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@consommations_bp.route('/consommations/<int:id>', methods=['PUT'])
@login_required
def update_consommation(id):
    """Mettre à jour une consommation (non facturée uniquement)"""
    if not current_user.has_permission('consommations'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        consommation = Consommation.query.get_or_404(id)
        
        # Empêcher la modification d'une consommation facturée
        if consommation.facture_id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Impossible de modifier une consommation facturée'}), 400
        
        data = request.get_json()
        
        # Si la quantité change, ajuster le stock
        if 'quantite' in data:
            nouvelle_quantite = int(data['quantite'])
            difference = nouvelle_quantite - consommation.quantite
            
            produit = consommation.produit
            
            # Vérifier le stock si augmentation
            if difference > 0 and produit.stock < difference:
                return jsonify({
                    'success': False,
                    'error': f'Stock insuffisant (disponible: {produit.stock})'
                }), 400
            
            # Ajuster le stock
            stock_avant = produit.stock
            produit.stock -= difference
            
            # Enregistrer le mouvement
            if difference != 0:
                stock_log = StockLog(
                    produit_id=produit.id,
                    type_mouvement='ajustement',
                    quantite=abs(difference),
                    stock_avant=stock_avant,
                    stock_apres=produit.stock,
                    utilisateur=current_user.username,
                    commentaire=f'Modification consommation #{consommation.id}'
                )
                db.session.add(stock_log)
            
            consommation.quantite = nouvelle_quantite
            consommation.montant_total = consommation.quantite * consommation.prix_unitaire
        
        if 'note' in data:
            consommation.note = data['note']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Consommation mise à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@consommations_bp.route('/consommations/<int:id>', methods=['DELETE'])
@login_required
def delete_consommation(id):
    """Supprimer une consommation (non facturée, admin uniquement)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        consommation = Consommation.query.get_or_404(id)
        
        # Empêcher la suppression d'une consommation facturée
        if consommation.facture_id:
            return jsonify({'success': False, 'error': 'Impossible de supprimer une consommation facturée'}), 400
        
        # Remettre le stock
        produit = consommation.produit
        stock_avant = produit.stock
        produit.stock += consommation.quantite
        
        # Enregistrer le mouvement
        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='entree',
            quantite=consommation.quantite,
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=f'Annulation consommation #{consommation.id}'
        )
        
        db.session.add(stock_log)
        db.session.delete(consommation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Consommation supprimée avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@consommations_bp.route('/consommations/statistiques', methods=['GET'])
@login_required
def get_statistiques_consommations():
    """Récupérer les statistiques des consommations"""
    try:
        date_debut = request.args.get('date_debut')
        date_fin = request.args.get('date_fin')
        
        query = Consommation.query
        
        if date_debut:
            date_d = datetime.fromisoformat(date_debut)
            query = query.filter(Consommation.date >= date_d)
        
        if date_fin:
            date_f = datetime.fromisoformat(date_fin)
            query = query.filter(Consommation.date <= date_f)
        
        consommations = query.all()
        
        # Produits les plus vendus
        produits_stats = {}
        for c in consommations:
            if c.produit_id not in produits_stats:
                produits_stats[c.produit_id] = {
                    'nom': c.produit.nom,
                    'quantite': 0,
                    'montant': 0
                }
            produits_stats[c.produit_id]['quantite'] += c.quantite
            produits_stats[c.produit_id]['montant'] += c.montant_total
        
        # Trier par quantité
        top_produits = sorted(
            produits_stats.values(),
            key=lambda x: x['quantite'],
            reverse=True
        )[:10]
        
        total_ventes = sum(c.montant_total for c in consommations)
        total_items = sum(c.quantite for c in consommations)
        
        return jsonify({
            'success': True,
            'data': {
                'total_consommations': len(consommations),
                'total_items_vendus': total_items,
                'montant_total_ventes': total_ventes,
                'top_produits': top_produits
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500