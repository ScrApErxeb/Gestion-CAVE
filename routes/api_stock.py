from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Produit, StockLog
from datetime import datetime

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/stock/mouvements', methods=['GET'])
@login_required
def get_mouvements_stock():
    """Récupérer l'historique des mouvements de stock"""
    try:
        produit_id = request.args.get('produit_id', '')
        type_mouvement = request.args.get('type_mouvement', '')
        date_debut = request.args.get('date_debut', '')
        date_fin = request.args.get('date_fin', '')
        
        query = StockLog.query
        
        if produit_id:
            query = query.filter_by(produit_id=int(produit_id))
        
        if type_mouvement:
            query = query.filter_by(type_mouvement=type_mouvement)
        
        if date_debut:
            date_d = datetime.fromisoformat(date_debut)
            query = query.filter(StockLog.date >= date_d)
        
        if date_fin:
            date_f = datetime.fromisoformat(date_fin)
            query = query.filter(StockLog.date <= date_f)
        
        mouvements = query.order_by(StockLog.date.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': m.id,
                'produit': m.produit.nom,
                'produit_id': m.produit_id,
                'type_mouvement': m.type_mouvement,
                'quantite': m.quantite,
                'stock_avant': m.stock_avant,
                'stock_apres': m.stock_apres,
                'date': m.date.isoformat(),
                'utilisateur': m.utilisateur,
                'commentaire': m.commentaire,
                'reference': m.reference
            } for m in mouvements]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@stock_bp.route('/stock/entree', methods=['POST'])
@login_required
def entree_stock():
    """Enregistrer une entrée de stock (réception de marchandise)"""
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('produit_id') or not data.get('quantite'):
            return jsonify({'success': False, 'error': 'Produit et quantité obligatoires'}), 400
        
        produit = Produit.query.get_or_404(data['produit_id'])
        quantite = int(data['quantite'])
        
        if quantite <= 0:
            return jsonify({'success': False, 'error': 'Quantité doit être positive'}), 400
        
        # Mise à jour du stock
        stock_avant = produit.stock
        produit.stock += quantite
        
        # Enregistrement du mouvement
        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='entree',
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=data.get('commentaire', 'Réception de marchandise'),
            reference=data.get('reference', '')
        )
        
        db.session.add(stock_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Entrée de stock enregistrée: +{quantite} {produit.unite}',
            'data': {
                'produit': produit.nom,
                'stock_avant': stock_avant,
                'stock_apres': produit.stock
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stock_bp.route('/stock/sortie', methods=['POST'])
@login_required
def sortie_stock():
    """Enregistrer une sortie de stock (perte, casse, don, etc.)"""
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('produit_id') or not data.get('quantite'):
            return jsonify({'success': False, 'error': 'Produit et quantité obligatoires'}), 400
        
        produit = Produit.query.get_or_404(data['produit_id'])
        quantite = int(data['quantite'])
        
        if quantite <= 0:
            return jsonify({'success': False, 'error': 'Quantité doit être positive'}), 400
        
        # Vérifier le stock disponible
        if produit.stock < quantite:
            return jsonify({
                'success': False,
                'error': f'Stock insuffisant (disponible: {produit.stock})'
            }), 400
        
        # Mise à jour du stock
        stock_avant = produit.stock
        produit.stock -= quantite
        
        # Enregistrement du mouvement
        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='sortie',
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=data.get('commentaire', 'Sortie de stock'),
            reference=data.get('reference', '')
        )
        
        db.session.add(stock_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Sortie de stock enregistrée: -{quantite} {produit.unite}',
            'data': {
                'produit': produit.nom,
                'stock_avant': stock_avant,
                'stock_apres': produit.stock
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stock_bp.route('/stock/ajustement', methods=['POST'])
@login_required
def ajustement_stock():
    """Ajuster le stock (inventaire, correction)"""
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('produit_id') or 'nouveau_stock' not in data:
            return jsonify({'success': False, 'error': 'Produit et nouveau stock obligatoires'}), 400
        
        produit = Produit.query.get_or_404(data['produit_id'])
        nouveau_stock = int(data['nouveau_stock'])
        
        if nouveau_stock < 0:
            return jsonify({'success': False, 'error': 'Le stock ne peut pas être négatif'}), 400
        
        # Calcul de la différence
        stock_avant = produit.stock
        difference = nouveau_stock - stock_avant
        
        # Mise à jour du stock
        produit.stock = nouveau_stock
        
        # Enregistrement du mouvement
        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='ajustement',
            quantite=abs(difference),
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=data.get('commentaire', f'Ajustement de stock: {difference:+d}'),
            reference=data.get('reference', 'Inventaire')
        )
        
        db.session.add(stock_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Stock ajusté: {difference:+d} {produit.unite}',
            'data': {
                'produit': produit.nom,
                'stock_avant': stock_avant,
                'stock_apres': produit.stock,
                'difference': difference
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stock_bp.route('/stock/inventaire', methods=['POST'])
@login_required
def inventaire_complet():
    """Effectuer un inventaire complet (ajustement de tous les produits)"""
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        # data doit contenir un tableau de {produit_id, stock_reel}
        if not data.get('inventaire') or not isinstance(data['inventaire'], list):
            return jsonify({'success': False, 'error': 'Format inventaire invalide'}), 400
        
        resultats = []
        
        for item in data['inventaire']:
            if not item.get('produit_id') or 'stock_reel' not in item:
                continue
            
            produit = Produit.query.get(item['produit_id'])
            if not produit:
                continue
            
            stock_reel = int(item['stock_reel'])
            stock_avant = produit.stock
            difference = stock_reel - stock_avant
            
            if difference != 0:
                # Mise à jour du stock
                produit.stock = stock_reel
                
                # Enregistrement du mouvement
                stock_log = StockLog(
                    produit_id=produit.id,
                    type_mouvement='inventaire',
                    quantite=abs(difference),
                    stock_avant=stock_avant,
                    stock_apres=produit.stock,
                    utilisateur=current_user.username,
                    commentaire=f'Inventaire: {difference:+d}',
                    reference=data.get('reference', f'INV-{datetime.now().strftime("%Y%m%d")}')
                )
                
                db.session.add(stock_log)
                
                resultats.append({
                    'produit': produit.nom,
                    'stock_avant': stock_avant,
                    'stock_reel': stock_reel,
                    'difference': difference
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Inventaire effectué: {len(resultats)} produits ajustés',
            'data': resultats
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stock_bp.route('/stock/alertes', methods=['GET'])
@login_required
def get_alertes_stock():
    """Récupérer les produits en stock critique"""
    try:
        produits_alertes = Produit.query.filter(
            Produit.stock <= Produit.stock_alerte,
            Produit.actif == True
        ).order_by(Produit.stock).all()
        
        return jsonify({
            'success': True,
            'count': len(produits_alertes),
            'data': [{
                'id': p.id,
                'code_produit': p.code_produit,
                'nom': p.nom,
                'stock': p.stock,
                'stock_alerte': p.stock_alerte,
                'unite': p.unite,
                'fournisseur': p.fournisseur.nom if p.fournisseur else None
            } for p in produits_alertes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@stock_bp.route('/stock/valeur', methods=['GET'])
@login_required
def get_valeur_stock():
    """Calculer la valeur totale du stock"""
    try:
        produits = Produit.query.filter_by(actif=True).all()
        
        valeur_achat = sum(p.stock * p.prix_achat for p in produits)
        valeur_vente = sum(p.stock * p.prix_vente for p in produits)
        marge_potentielle = valeur_vente - valeur_achat
        
        return jsonify({
            'success': True,
            'data': {
                'valeur_achat': valeur_achat,
                'valeur_vente': valeur_vente,
                'marge_potentielle': marge_potentielle,
                'total_produits': len(produits),
                'total_items': sum(p.stock for p in produits)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500