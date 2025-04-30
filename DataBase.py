from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Inicijuojame db instanciją (bus sujungta su Flask app vėliau)
db = SQLAlchemy()

class TranslationMemory(db.Model):
    __tablename__ = 'translation_memory'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=True)
    translation = db.Column(db.Text, nullable=True)
    source_lang = db.Column(db.String(10), nullable=False)
    target_lang = db.Column(db.String(10), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    is_document = db.Column(db.Boolean, default=False)
    file_path = db.Column(db.String(255), nullable=True)  # Saugo .docx ar kito failo kelią
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TranslationMemory {self.id} | {self.source_lang}->{self.target_lang} | confirmed={self.confirmed}>"
