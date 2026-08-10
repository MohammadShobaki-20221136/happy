import os
from collections import Counter
from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
from flask import Flask, request, jsonify, render_template

from app.main import (
    insert_user,
    check_if_exist,
    get_user_by_email,
    get_user_id,
    update_last_login,
    get_history_by_user,
    delete_history,
    analyze_and_save,
)


app = Flask(__name__)
# NOTE: replace with a real secret (e.g. loaded from an environment variable)
# before deploying anywhere outside of local development.
SECRET_KEY = "Mohammad_Shobaki"
ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# JSON serialization helpers
# (SQLAlchemy rows come back with UUID / datetime objects, which
#  jsonify can't handle on its own)
# ---------------------------------------------------------------------------

def serialize_user(user):
    if user is None:
        return None
    return {
        "user_id": str(user["user_id"]),
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "last_login": user["last_login"].isoformat() if user.get("last_login") else None,
    }


def serialize_history_row(row):
    return {
        "id": str(row["id"]),
        "input_text": row["input_text"],
        "sentiment_label": row["sentiment_label"],
        "confidence_score": row["confidence_score"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed access token."}), 401
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify and decode the payload
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Inject token claims into request context for route use
            request.user_id = payload.get("sub")
            request.user_email = payload.get("email")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Access token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid or tampered access token."}), 401

        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# static page routes (plain HTML, no templating - JS handles the rest)
# ---------------------------------------------------------------------------

@app.route("/")
def base():
    return render_template("login.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/analyze")
def analyze_page():
    return render_template("analyze.html")


@app.route("/profile")
def profile_page():
    return render_template("profile.html")


# ---------------------------------------------------------------------------
# API: auth
# ---------------------------------------------------------------------------

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are all required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    if get_user_by_email(email):
        return jsonify({"error": "An account with that email already exists."}), 409

    user_id = insert_user(name=name, email=email, password=password)
    
    # Generate token immediately upon registration
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return jsonify({
        "token": token,
        "user_id": str(user_id), 
        "name": name, 
        "email": email
    }), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    if not check_if_exist(email, password):
        return jsonify({"error": "Invalid email or password."}), 401

    user_id = get_user_id(email)
    update_last_login(user_id)

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2), 
        "iat": datetime.now(timezone.utc)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return jsonify({
        "token": token,
        "user_id": str(user_id), 
        "email": email
    }), 200


@app.route("/api/logout", methods=["POST"])
def api_logout():
    # Stateless applications do not clear sessions server-side.
    # Client-side JavaScript must delete the saved token.
    return jsonify({"message": "Logged out server-side. Please discard client token."}), 200


@app.route("/api/session", methods=["GET"])
def api_session():
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"authenticated": False}), 200
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return jsonify({"authenticated": True, "email": payload.get("email")}), 200
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"authenticated": False}), 200


# ---------------------------------------------------------------------------
# API: analyze
# ---------------------------------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
@login_required
def api_analyze():
    data = request.get_json(silent=True) or {}
    input_text = (data.get("input_text") or "").strip()

    if not input_text:
        return jsonify({"error": "input_text is required."}), 400
    if len(input_text) > 1000:
        return jsonify({"error": "input_text must be 1000 characters or fewer."}), 400

    result = analyze_and_save(request.user_id, input_text)
    result["history_id"] = str(result["history_id"])
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# API: history
# ---------------------------------------------------------------------------

@app.route("/api/history", methods=["GET"])
@login_required
def api_history():
    rows = get_history_by_user(request.user_id)
    return jsonify([serialize_history_row(r) for r in rows]), 200


@app.route("/api/history/<history_id>", methods=["DELETE"])
@login_required
def api_delete_history(history_id):
    delete_history(history_id)
    return jsonify({"message": "Deleted."}), 200


# ---------------------------------------------------------------------------
# API: profile
# ---------------------------------------------------------------------------

@app.route("/api/profile", methods=["GET"])
@login_required
def api_profile():
    user = get_user_by_email(request.user_email)
    rows = get_history_by_user(request.user_id)

    total_analyses = len(rows)
    if rows:
        counts = Counter(r["sentiment_label"] for r in rows)
        most_common = counts.most_common(1)[0][0]
        avg_confidence = round(
            sum(r["confidence_score"] for r in rows) / total_analyses * 100
        )
    else:
        most_common = None
        avg_confidence = 0

    return jsonify({
        "user": serialize_user(user),
        "stats": {
            "total_analyses": total_analyses,
            "most_common": most_common,
            "avg_confidence": avg_confidence,
        },
    }), 200


if __name__ == "__main__":
    app.run(debug=True)
