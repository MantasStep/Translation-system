# app/db/models.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pwd_hash   = db.Column(db.String(128), nullable=False)
    role       = db.Column(db.String(10), nullable=False, default="USER")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    password_hash = db.Column(db.String(128), nullable=False)

    translations = db.relationship(
        "TranslationMemory",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class TranslationMemory(db.Model):
    __tablename__ = 'translation_memory'

    id = db.Column(db.Integer, primary_key=True)
    source_text = db.Column(db.Text, nullable=True)
    translated_text = db.Column(db.Text, nullable=True)
    source_lang = db.Column(db.String(10))
    target_lang = db.Column(db.String(10))
    is_document = db.Column(db.Boolean, default=False)
    file_path = db.Column(db.String(256))
    translated_path = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user    = db.relationship('User', backref='translations')

    def __repr__(self):
        return f"<TM {self.id} {self.source_lang}->{self.target_lang}>"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="translations"
    )