from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Produit, Categorie, Fournisseur
from datetime import datetime

produits_bp = Blueprint('produits', __name__)

@produits_bp.route('/produits', methods=['GET'])
@login_required
def get_produits():
    """Récupérer tous les produits avec filtres et pagination"""
    try:
        recherche = request.args.get('recherche', '')
        actif = request.args.get('actif', 'true').lower() == 'true'
        stock_critique = request.args.get('stock_critique', '').lower() == 'true'
        categorie_id = request.args.get('categorie_id')
        fournisseur_id = request.args.get('fournisseur_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        query = Produit.query

        if actif:
            query = query.filter_by(actif=True)
        if stock_critique:
            query = query.filter(Produit.stock <= Produit.stock_alerte)
        if recherche:
            pattern = f"%{recherche}%"
            query = query.filter(
                db.or_(
                    Produit.code_produit.like(pattern),
                    Produit.nom.like(pattern),
                    Produit.type.like(pattern)
                )
            )
        if categorie_id:
            query = query.filter_by(categorie_id=int(categorie_id))
        if fournisseur_id:
            query = query.filter_by(fournisseur_id=int(fournisseur_id))

        pagination = query.order_by(Produit.nom).paginate(page=page, per_page=per_page)
        produits = pagination.items
        for p in produits:
            print(">>>", p.nom, p.stock, p.stock_alerte, "CRITIQUE:", p.stock_critique)

        return jsonify({
            'success': True,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page,
            'data': [{
                'id': p.id,
                'code_produit': p.code_produit,
                'nom': p.nom,
                'type': p.type,
                'prix_achat': p.prix_achat,
                'prix_vente': p.prix_vente,
                'stock': p.stock,
                'stock_alerte': p.stock_alerte,
                'unite': p.unite,
                'actif': p.actif,
                'categorie': p.categorie.nom if p.categorie else None,
                'fournisseur': p.fournisseur.nom if p.fournisseur else None,
                'marge': p.marge,
                'marge_pourcentage': p.marge_pourcentage,
                'stock_critique': p.stock_critique
            } for p in produits]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/produits/<int:id>', methods=['GET'])
@login_required
def get_produit(id):
    """Récupérer un produit spécifique"""
    try:
        produit = Produit.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id': produit.id,
                'code_produit': produit.code_produit,
                'nom': produit.nom,
                'type': produit.type,
                'prix_achat': produit.prix_achat,
                'prix_vente': produit.prix_vente,
                'stock': produit.stock,
                'stock_alerte': produit.stock_alerte,
                'unite': produit.unite,
                'actif': produit.actif,
                'categorie_id': produit.categorie_id,
                'fournisseur_id': produit.fournisseur_id,
                'marge': produit.marge,
                'marge_pourcentage': produit.marge_pourcentage,
                'stock_critique': produit.stock_critique
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/produits', methods=['POST'])
@login_required
def create_produit():
    if not current_user.has_permission('produits'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        data = request.get_json()

        # Validation des champs numériques
        try:
            prix_vente = float(data['prix_vente'])
            prix_achat = float(data.get('prix_achat', 0))
            stock = int(data.get('stock', 0))
            stock_alerte = int(data.get('stock_alerte', 10))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Prix, stock et stock alerte doivent être des nombres valides'}), 400

        # Vérifier l'existence de la catégorie et du fournisseur
        if data.get('categorie_id') and not Categorie.query.get(data['categorie_id']):
            return jsonify({'success': False, 'error': 'Catégorie invalide'}), 400
        if data.get('fournisseur_id') and not Fournisseur.query.get(data['fournisseur_id']):
            return jsonify({'success': False, 'error': 'Fournisseur invalide'}), 400

        # Générer un code produit si nécessaire
        if data.get('code_produit'):
            if Produit.query.filter_by(code_produit=data['code_produit']).first():
                return jsonify({'success': False, 'error': 'Code produit déjà utilisé'}), 400
        else:
            dernier = Produit.query.order_by(Produit.id.desc()).first()
            prochain_num = (dernier.id + 1) if dernier else 1
            data['code_produit'] = f'PRD{prochain_num:05d}'

        # Créer le produit sans setter marge/marge_pourcentage
        produit = Produit(
        code_produit=data['code_produit'],
        nom=data['nom'],
        type=data.get('type', ''),
        prix_achat=prix_achat,
        prix_vente=prix_vente,
        stock=stock,
        stock_alerte=stock_alerte,
        unite=data.get('unite', 'unité'),
        categorie_id=data.get('categorie_id'),
        fournisseur_id=data.get('fournisseur_id')
    )

        db.session.add(produit)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Produit créé avec succès',
            'data': {
                'id': produit.id,
                'code_produit': produit.code_produit,
                'nom': produit.nom
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/produits/<int:id>', methods=['PUT'])
@login_required
def update_produit(id):
    if not current_user.has_permission('produits'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403

    try:
        produit = Produit.query.get_or_404(id)
        data = request.get_json()

        # Mise à jour des champs numériques
        if 'prix_vente' in data:
            try:
                produit.prix_vente = float(data['prix_vente'])
            except ValueError:
                return jsonify({'success': False, 'error': 'Prix vente invalide'}), 400
        if 'prix_achat' in data:
            try:
                produit.prix_achat = float(data['prix_achat'])
            except ValueError:
                return jsonify({'success': False, 'error': 'Prix achat invalide'}), 400
        if 'stock' in data:
            try:
                produit.stock = int(data['stock'])
            except ValueError:
                return jsonify({'success': False, 'error': 'Stock invalide'}), 400
        if 'stock_alerte' in data:
            try:
                produit.stock_alerte = int(data['stock_alerte'])
            except ValueError:
                return jsonify({'success': False, 'error': 'Stock alerte invalide'}), 400

        # Vérifier existence catégorie/fournisseur
        if 'categorie_id' in data and data['categorie_id']:
            if not Categorie.query.get(data['categorie_id']):
                return jsonify({'success': False, 'error': 'Catégorie invalide'}), 400
            produit.categorie_id = data['categorie_id']

        if 'fournisseur_id' in data and data['fournisseur_id']:
            if not Fournisseur.query.get(data['fournisseur_id']):
                return jsonify({'success': False, 'error': 'Fournisseur invalide'}), 400
            produit.fournisseur_id = data['fournisseur_id']

        # Mise à jour des autres champs
        for champ in ['nom', 'type', 'unite', 'actif']:
            if champ in data:
                setattr(produit, champ, data[champ])

        # Recalcul automatique de la marge

        db.session.commit()

        return jsonify({'success': True, 'message': 'Produit mis à jour avec succès', 'data': {'id': produit.id, 'code_produit': produit.code_produit, 'nom': produit.nom}})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/produits/<int:id>', methods=['DELETE'])
@login_required
def delete_produit(id):
    """Désactiver un produit (soft delete)"""
    if not current_user.has_permission('produits'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        produit = Produit.query.get_or_404(id)
        produit.actif = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produit désactivé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Récupérer toutes les catégories"""
    try:
        categories = Categorie.query.order_by(Categorie.nom).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': c.id,
                'nom': c.nom,
                'description': c.description
            } for c in categories]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/categories', methods=['POST'])
@login_required
def create_categorie():
    """Créer une nouvelle catégorie"""
    if not current_user.has_permission('produits'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        if not data.get('nom'):
            return jsonify({'success': False, 'error': 'Nom obligatoire'}), 400
        
        categorie = Categorie(
            nom=data['nom'],
            description=data.get('description', '')
        )
        
        db.session.add(categorie)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Catégorie créée avec succès',
            'data': {'id': categorie.id, 'nom': categorie.nom}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/fournisseurs', methods=['GET'])
@login_required
def get_fournisseurs():
    """Récupérer tous les fournisseurs"""
    try:
        fournisseurs = Fournisseur.query.order_by(Fournisseur.nom).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': f.id,
                'nom': f.nom,
                'telephone': f.telephone,
                'adresse': f.adresse,
                'email': f.email
            } for f in fournisseurs]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@produits_bp.route('/fournisseurs', methods=['POST'])
@login_required
def create_fournisseur():
    """Créer un nouveau fournisseur"""
    if not current_user.has_permission('produits'):
        return jsonify({'success': False, 'error': 'Permission refusée'}), 403
    
    try:
        data = request.get_json()
        
        if not data.get('nom'):
            return jsonify({'success': False, 'error': 'Nom obligatoire'}), 400
        
        fournisseur = Fournisseur(
            nom=data['nom'],
            telephone=data.get('telephone', ''),
            adresse=data.get('adresse', ''),
            email=data.get('email', '')
        )
        
        db.session.add(fournisseur)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Fournisseur créé avec succès',
            'data': {'id': fournisseur.id, 'nom': fournisseur.nom}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
