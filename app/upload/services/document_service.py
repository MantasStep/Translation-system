# app/upload/services/document_service.py

import os
from flask import current_app
from docx import Document
from app.database.models import TranslationMemory
from flask_login import current_user
from app import db

# Hardcoded path locations
UPLOAD_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\uploads"
TRANSLATED_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations"

class DocumentService:

    def save_original(self, file):
        folder = UPLOAD_FOLDER
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, file.filename)
        file.save(path)
        return path

    def translate_docx(self, input_path: str, output_path: str, translate_fn, src_lang, tgt_lang):
        doc = Document(input_path)
        
        for para in doc.paragraphs:
            if para.text.strip():
                translated = translate_fn(para.text)
                memory = TranslationMemory(
                    source_text=para.text,
                    translated_text=translated,
                    source_lang=src_lang,
                    target_lang=tgt_lang,
                    is_document=True,
                    file_path=input_path,
                    translated_path=output_path,
                    user_id=current_user.id
                )
                db.session.add(memory)

        db.session.commit()
        doc.save(output_path)
        return output_path

    def get_upload_path(self, filename):
        return os.path.join(UPLOAD_FOLDER, filename)

    def get_translation_path(self, filename):
        return os.path.join(TRANSLATED_FOLDER, f"test_translated_{filename}")
