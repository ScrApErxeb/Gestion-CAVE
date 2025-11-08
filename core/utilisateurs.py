from models import db, User
from werkzeug.security import check_password_hash
import secrets
import datetime

# Mémoire temporaire pour les sessions locales
sessions = {}

def verifier_connexion(username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    token = secrets.token_hex(16)
    sessions[token] = {
        "user_id": user.id,
        "expiration": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return {"token": token}

def verifier_session(token):
    data = sessions.get(token)
    if not data:
        return None
    if datetime.datetime.utcnow() > data["expiration"]:
        del sessions[token]
        return None
    return data["user_id"]
