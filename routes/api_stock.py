from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Produit, StockLog
from datetime import datetime

stock_bp = Blueprint('stock', __name__)

# --- UTILITAIRES ---
def parse_int(value, default=None):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None

def generate_reference(prefix='STK'):
    return f'{prefix}-{datetime.now().strftime("%Y%m%d%H%M%S")}'

# --- MOUVEMENTS DE STOCK ---
@stock_bp.route('/stock/mouvements', methods=['GET'])
@login_required
def get_mouvements_stock():
    """Récupérer l'historique des mouvements de stock avec pagination et filtrage"""
    try:
        query = StockLog.query

        produit_id = parse_int(request.args.get('produit_id'))
        type_mouvement = request.args.get('type_mouvement', '')
        utilisateur = request.args.get('utilisateur', '')
        date_debut = parse_date(request.args.get('date_debut'))
        date_fin = parse_date(request.args.get('date_fin'))
        page = parse_int(request.args.get('page'), 1)
        per_page = parse_int(request.args.get('per_page'), 50)

        if produit_id:
            query = query.filter_by(produit_id=produit_id)
        if type_mouvement:
            query = query.filter_by(type_mouvement=type_mouvement)
        if utilisateur:
            query = query.filter(StockLog.utilisateur.like(f'%{utilisateur}%'))
        if date_debut:
            query = query.filter(StockLog.date >= date_debut)
        if date_fin:
            query = query.filter(StockLog.date <= date_fin)

        pagination = query.order_by(StockLog.date.desc()).paginate(page=page, per_page=per_page)
        mouvements = pagination.items

        return jsonify({
            'success': True,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
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

# --- ENTRÉE DE STOCK ---
@stock_bp.route('/stock/entree', methods=['POST'])
@login_required
def entree_stock():
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        data = request.get_json()
        produit_id = parse_int(data.get('produit_id'))
        quantite = parse_int(data.get('quantite'))

        if not produit_id or not quantite:
            return jsonify({'success': False, 'error': 'Produit et quantité obligatoires'}), 400
        if quantite <= 0:
            return jsonify({'success': False, 'error': 'Quantité doit être positive'}), 400

        produit = Produit.query.get_or_404(produit_id)
        stock_avant = produit.stock
        produit.stock += quantite  # stock_critique est calculé automatiquement

        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='entree',
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=data.get('commentaire', 'Réception de marchandise'),
            reference=data.get('reference', generate_reference('ENT'))
        )

        db.session.add(stock_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Entrée de stock enregistrée: +{quantite} {produit.unite}',
            'data': {'produit': produit.nom, 'stock_avant': stock_avant, 'stock_apres': produit.stock}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# --- SORTIE DE STOCK ---
@stock_bp.route('/stock/sortie', methods=['POST'])
@login_required
def sortie_stock():
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        data = request.get_json()
        produit_id = parse_int(data.get('produit_id'))
        quantite = parse_int(data.get('quantite'))

        if not produit_id or not quantite:
            return jsonify({'success': False, 'error': 'Produit et quantité obligatoires'}), 400
        if quantite <= 0:
            return jsonify({'success': False, 'error': 'Quantité doit être positive'}), 400

        produit = Produit.query.get_or_404(produit_id)
        if produit.stock < quantite:
            return jsonify({'success': False, 'error': f'Stock insuffisant (disponible: {produit.stock})'}), 400

        stock_avant = produit.stock
        produit.stock -= quantite  # stock_critique est calculé automatiquement

        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='sortie',
            quantite=quantite,
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=data.get('commentaire', 'Sortie de stock'),
            reference=data.get('reference', generate_reference('SRT'))
        )

        db.session.add(stock_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Sortie de stock enregistrée: -{quantite} {produit.unite}',
            'data': {'produit': produit.nom, 'stock_avant': stock_avant, 'stock_apres': produit.stock}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# --- AJUSTEMENT DE STOCK ---
@stock_bp.route('/stock/ajustement', methods=['POST'])
@login_required
def ajustement_stock():
    if not current_user.has_permission('stock'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        data = request.get_json()
        produit_id = parse_int(data.get('produit_id'))
        nouveau_stock = parse_int(data.get('nouveau_stock'))

        if not produit_id or nouveau_stock is None:
            return jsonify({'success': False, 'error': 'Produit et nouveau stock obligatoires'}), 400
        if nouveau_stock < 0:
            return jsonify({'success': False, 'error': 'Le stock ne peut pas être négatif'}), 400

        produit = Produit.query.get_or_404(produit_id)
        stock_avant = produit.stock
        difference = nouveau_stock - stock_avant
        produit.stock = nouveau_stock  # stock_critique est calculé automatiquement

        stock_log = StockLog(
            produit_id=produit.id,
            type_mouvement='ajustement',
            quantite=abs(difference),
            stock_avant=stock_avant,
            stock_apres=produit.stock,
            utilisateur=current_user.username,
            commentaire=data.get('commentaire', f'Ajustement de stock: {difference:+d}'),
            reference=data.get('reference', generate_reference('ADJ'))
        )

        db.session.add(stock_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Stock ajusté: {difference:+d} {produit.unite}',
            'data': {'produit': produit.nom, 'stock_avant': stock_avant, 'stock_apres': produit.stock, 'difference': difference}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- ALERTES ET VALEUR STOCK ---
@stock_bp.route('/stock/alertes', methods=['GET'])
@login_required
def get_alertes_stock():
    try:
        produits_alertes = Produit.query.filter(
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
