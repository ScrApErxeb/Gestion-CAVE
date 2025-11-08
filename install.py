"""
Script d'installation automatique pour Cave Gestion
Crée tous les dossiers nécessaires et vérifie les dépendances
"""

import os
import sys
import subprocess

def create_directory(path):
    """Créer un dossier s'il n'existe pas"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✓ Dossier créé: {path}")
    else:
        print(f"✓ Dossier existant: {path}")

def create_file(path, content=""):
    """Créer un fichier s'il n'existe pas"""
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fichier créé: {path}")
    else:
        print(f"✓ Fichier existant: {path}")

def install_dependencies():
    """Installer les dépendances Python"""
    print("\n📦 Installation des dépendances...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de l'installation des dépendances")
        return False

def main():
    print("=" * 60)
    print("🍷 INSTALLATION DE CAVE GESTION")
    print("=" * 60)
    
    # Vérifier Python
    print(f"\n✓ Python {sys.version}")
    
    # Créer la structure des dossiers
    print("\n📁 Création de la structure des dossiers...")
    folders = [
        'database',
        'routes',
        'core',
        'static',
        'templates',
        'backups'
    ]
    
    for folder in folders:
        create_directory(folder)
    
    # Créer les fichiers __init__.py pour les modules Python
    print("\n📝 Création des fichiers de modules...")
    init_files = [
        'routes/__init__.py',
        'core/__init__.py'
    ]
    
    for init_file in init_files:
        create_file(init_file, "# Module Python\n")
    
    # Créer un fichier .gitignore
    print("\n📝 Création du fichier .gitignore...")
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Database
*.db
database/*.db
backups/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""
    create_file('.gitignore', gitignore_content)
    
    # Vérifier requirements.txt
    if os.path.exists('requirements.txt'):
        print("\n✓ requirements.txt trouvé")
        
        # Demander si on installe les dépendances
        response = input("\n❓ Voulez-vous installer les dépendances maintenant? (o/n): ")
        if response.lower() == 'o':
            if install_dependencies():
                print("\n✅ Installation terminée avec succès!")
            else:
                print("\n⚠️ Installation terminée avec des erreurs")
                print("   Essayez: pip install -r requirements.txt")
        else:
            print("\n⚠️ N'oubliez pas d'installer les dépendances:")
            print("   pip install -r requirements.txt")
    else:
        print("\n❌ requirements.txt non trouvé!")
        print("   Créez ce fichier avec les dépendances nécessaires")
    
    # Instructions finales
    print("\n" + "=" * 60)
    print("🎉 INSTALLATION TERMINÉE")
    print("=" * 60)
    print("\n📋 Prochaines étapes:")
    print("   1. Assurez-vous que tous les fichiers sont en place:")
    print("      - app.py")
    print("      - models.py")
    print("      - routes/api_*.py")
    print("      - templates/*.html")
    print("      - static/style.css")
    print("   2. Lancez l'application: python app.py")
    print("   3. Connectez-vous avec: admin / admin123")
    print("\n💡 Conseil: Changez le mot de passe admin après la première connexion!")
    print("=" * 60)

if __name__ == "__main__":
    main()