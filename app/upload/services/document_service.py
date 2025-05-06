# app/upload/services/document_service.py

import os
from flask import current_app
from docx import Document

class DocumentService:

    def save_original(self, file):
        folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, file.filename)
        file.save(path)
        return path

    def translate_docx(self, input_path: str, output_path: str, translate_fn):
        """
        Atidaro input_path docx, pereina per kiekvieną paragrafą,
        translate_fn(text) -> translated_text, pakeičia tik tekstą,
        o visos nuotraukos / lentelės / formatavimas lieka.
        Išsaugo output_path.
        """
        doc = Document(input_path)
        for para in doc.paragraphs:
            if para.text.strip():
                # translate_fn turi priimti vieną string'ą
                translated = translate_fn(para.text)
                # pakeičiame VISĄ paragrafą nauju tekstu:
                para.text = translated
        doc.save(output_path)
        return output_path

    def load_txt_paragraphs(self, path) -> list[str]:
        text = open(path, encoding="utf-8").read()
        return [p for p in text.split("\n\n") if p.strip()]
