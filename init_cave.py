from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import webbrowser, threading, os
from models import db, Abonne, Produit, Vente, Paiement
from datetime import timedelta
from models import db, User
from werkzeug.security import generate_password_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cave.db")


app = Flask(__name__)
app.secret_key = "cave_secret"
app.permanent_session_lifetime = timedelta(hours=1)

# créer le dossier database s'il n'existe pas
os.makedirs("database", exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password_hash=generate_password_hash("admin"))
        db.session.add(admin)
        db.session.commit()
        print("Utilisateur admin/admin créé.")
    else:
        print("Admin déjà existant.")



# --- AUTH ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("pwd")
        if user == "admin" and pwd == "admin":
            session.permanent = True
            session["user"] = user
            return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# --- PAGE PRINCIPALE ---
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route("/page/<string:nom>")
def page(nom):
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template(f"{nom}.html")


# --- LANCEMENT ---
def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(debug=False)
