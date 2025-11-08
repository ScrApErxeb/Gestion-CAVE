# 🚀 Guide de démarrage rapide - Cave Gestion

## Installation rapide (5 minutes)

### 1. Prérequis
- Python 3.8+ installé sur votre ordinateur
- Connexion internet (pour l'installation initiale uniquement)

### 2. Installation

```bash
# 1. Télécharger et extraire le projet
# 2. Ouvrir un terminal dans le dossier du projet

# 3. Exécuter le script d'installation
python install.py

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer l'application
python app.py
```

Le navigateur s'ouvrira automatiquement sur `http://127.0.0.1:5000/`

### 3. Première connexion

**Identifiants par défaut:**
- **Utilisateur**: `admin`
- **Mot de passe**: `admin123`

⚠️ **IMPORTANT**: Changez ce mot de passe immédiatement !

---

## 🎯 Premiers pas

### 1. Créer des catégories et fournisseurs
1. Aller dans **Produits**
2. Cliquer sur **Catégories** (si disponible) ou créer directement des produits

### 2. Ajouter des produits
1. Cliquer sur **+ Nouveau produit**
2. Remplir: nom, prix achat, prix vente, stock initial
3. Enregistrer

### 3. Créer des abonnés
1. Aller dans **Abonnés**
2. Cliquer sur **+ Nouvel abonné**
3. Remplir: nom, téléphone (obligatoires)
4. Enregistrer

### 4. Enregistrer une vente
1. Aller dans **Consommations**
2. Sélectionner: abonné + produit + quantité
3. Cliquer sur **Enregistrer la vente**
4. Le stock se met à jour automatiquement

### 5. Créer une facture
1. Aller dans **Factures**
2. Cliquer sur **+ Nouvelle facture**
3. Sélectionner un abonné
4. Cocher les consommations à facturer
5. Créer la facture

### 6. Enregistrer un paiement
1. Aller dans **Paiements**
2. Cliquer sur **+ Nouveau paiement**
3. Sélectionner la facture
4. Entrer le montant et le mode de paiement
5. Enregistrer

---

## 📊 Navigation

### Tableau de bord
- Vue d'ensemble de l'activité
- Statistiques clés
- Alertes de stock

### Abonnés
- Liste complète des clients
- Ajout/modification
- Suivi des soldes dus

### Consommations
- Enregistrement des ventes
- Historique des transactions
- Ventes en attente de facturation

### Produits
- Catalogue de produits
- Gestion des prix
- Alertes de stock critique

### Stock
- Entrées/sorties
- Ajustements d'inventaire
- Historique des mouvements

### Factures
- Création de factures
- Suivi des paiements
- Factures impayées

### Paiements
- Enregistrement des règlements
- Modes de paiement multiples
- Historique complet

---

## ⚙️ Configuration rapide

### Modifier les paramètres de la cave
Actuellement via la base de données (table `parametres_globaux`):
- Nom de la cave
- Adresse, téléphone, email
- Taux de TVA (par défaut: 18%)

### Créer un nouvel utilisateur

```python
# Ouvrir une console Python
python

# Dans la console Python:
from app import app
from models import db, User

with app.app_context():
    # Créer un caissier
    user = User(
        username='caissier1',
        role='caissier',
        nom_complet='Jean Dupont'
    )
    user.set_password('motdepasse123')
    db.session.add(user)
    db.session.commit()
    print("Utilisateur créé!")
```

---

## 🔧 Résolution rapide de problèmes

### Erreur "Module not found"
```bash
pip install -r requirements.txt
```

### Erreur de base de données
```bash
# Supprimer la base et relancer
rm database/cave.db
python app.py
```

### Le navigateur ne s'ouvre pas
Ouvrir manuellement: `http://127.0.0.1:5000/`

### Port déjà utilisé
Modifier dans `app.py` la dernière ligne:
```python
app.run(debug=True, port=5001)  # Changer le port
```

---

## 💾 Sauvegarde rapide

```bash
# Windows
copy database\cave.db database\cave_backup_%date%.db

# Linux/Mac
cp database/cave.db database/cave_backup_$(date +%Y%m%d).db
```

---

## 📞 Support rapide

### Problème courant: Stock négatif
- Vérifier les quantités saisies
- Faire un ajustement de stock si nécessaire

### Problème: Facture incorrecte
- Seul l'admin peut supprimer une facture
- Créer une nouvelle facture si nécessaire

### Problème: Mot de passe oublié
Réinitialiser via Python:
```python
from app import app
from models import db, User

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    user.set_password('nouveau_mdp')
    db.session.commit()
```

---

## 🎓 Bonnes pratiques

1. **Sauvegardez régulièrement** la base de données
2. **Changez les mots de passe** par défaut
3. **Formez les utilisateurs** aux différents rôles
4. **Vérifiez les stocks** régulièrement
5. **Faites des inventaires** mensuels
6. **Suivez les factures impayées** de près

---

## 🚀 Aller plus loin

### Personnalisation avancée
- Modifier `static/style.css` pour changer l'apparence
- Ajouter des catégories de produits personnalisées
- Créer des rapports personnalisés

### Intégration
- Exporter les données vers Excel (à venir)
- Imprimer des factures (à venir)
- Génération de rapports PDF (à venir)

---

**Bonne utilisation de Cave Gestion ! 🍷**