import os
import json
import re
import hashlib
import secrets

class UserAuthManager:
    DB_PATH = "users_db.json"
    
    @classmethod
    def _load(cls):
        if not os.path.exists(cls.DB_PATH): return {}
        try:
            with open(cls.DB_PATH, "r") as f: return json.load(f)
        except: return {}
        
    @classmethod
    def _save(cls, db):
        with open(cls.DB_PATH, "w") as f: json.dump(db, f)

    @staticmethod
    def is_valid_email(email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    @classmethod
    def register(cls, email, password):
        if not email or not password: return "❌ Email/password empty."
        if not cls.is_valid_email(email): return "❌ Invalid email format."
        
        db = cls._load()
        if email in db: return "❌ User already exists."
        
        token = secrets.token_hex(4).upper() # 8-char code
        db[email] = {
            "pwd": hashlib.sha256(password.encode()).hexdigest(),
            "verified": True, # Automatically verified for now
            "token": token
        }
        cls._save(db)
        
        return f"✅ Registered successfully! You can now login with {email}."

    @classmethod
    def verify_token(cls, email, token):
        # Kept for compatibility but verification is now automatic
        return "✅ Account verified!"

    @classmethod
    def login(cls, email, password):
        db = cls._load()
        if email not in db: return False, "❌ Email not found."
        user = db[email]
        if user["pwd"] != hashlib.sha256(password.encode()).hexdigest():
            return False, "❌ Incorrect password."
        # Verification check removed per user request
        return True, "✅ Success"
