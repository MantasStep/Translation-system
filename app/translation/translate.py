# app/translation/translate.py

import os
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from docx import Document
from app.translation.services.translation_service import TranslationService
from flask_login import login_required
from app.upload.services.document_service import DocumentService
from app.translation.constants import HF_MODELS

translation_bp = Blueprint("translation", __name__,
                           template_folder="templates",
                           url_prefix="/translate")

UPLOAD_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\uploads"
TRANSLATED_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations"

svc = TranslationService()
document_service = DocumentService() 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@translation_bp.route("/", methods=["GET"])
@login_required
def translate_page():
    direction = request.args.get("direction", "")
    print(f"🔍 Kryptis pasirinkta: {direction}")
    return render_template("translate.html")


@translation_bp.route("/translate", methods=["POST"])
def translate_api():
    try:
        data = request.json
        print(f"📥 Gauta užklausa su duomenimis: {data}")
        src, tgt = data["direction"].split("-")
        best, candidates = svc.translate_text(data["text"], src, tgt)

        svc.save_translation(
            original=data["text"],
            best=best,
            all_outs=candidates,
            src=src,
            tgt=tgt,
            is_doc=False
        )

        result = {
            "translated_text": best,
            "candidates": [
                {"model": model, "translation": translation} 
                for model, translation in candidates.items()
            ]
        }
        print(f"✅ Vertimo rezultatas: {result}")
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Klaida vertime: {str(e)}")
        return jsonify({"error": str(e)}), 500

@translation_bp.route("/upload", methods=["POST"])
@login_required
def upload_and_translate():
    uploaded = request.files.get("file", None)
    if not uploaded:
        return ("Nėra įkeltas failas", 400)

    direction = request.form.get("direction", "")
    try:
        src, tgt = direction.split("-")
    except ValueError:
        return ("Neteisinga kryptis", 400)

    orig_name = uploaded.filename
    uid       = uuid.uuid4().hex
    base, ext = os.path.splitext(orig_name)

    upl_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upl_dir, exist_ok=True)
    input_path = os.path.join(upl_dir, f"{uid}{ext}")
    uploaded.save(input_path)

    out_dir = current_app.config["TRANSLATED_FOLDER"]
    os.makedirs(out_dir, exist_ok=True)
    out_name = f"test_translated_{uid}{ext}"
    output_path = os.path.join(out_dir, out_name)

    if ext.lower() == ".txt":
        text = open(input_path, encoding="utf-8").read()
        best, _ = svc.translate_text(text, src, tgt)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(best)

    elif ext.lower() == ".docx":
        doc = Document(input_path)
        for p in doc.paragraphs:
            if p.text.strip():
                translated, _ = svc.translate_text(p.text, src, tgt)
                p.text = translated
        doc.save(output_path)

    else:
        return ("Nepalaikomas failo tipas", 400)
    
    svc.save_translation(
        original=None,
        best=None,
        all_outs={},
        src=src,
        tgt=tgt,
        is_doc=True,
        file_path=input_path,
        translated_path=output_path
    )

    download_url = f"/download/{out_name}"
    print(f"🔍 Generuotas kelias: /download/{out_name}")
    print(f"🔍 Ar failas egzistuoja? {os.path.exists(output_path)}")

    return jsonify({"download_url": download_url, "status": "ok"})
    
@translation_bp.route("/download/<filename>", methods=["GET"])
def download_translated_file(filename):
    print(f"🔍 Bandome parsiųsti failą: {filename}")

    file_path = os.path.join(TRANSLATED_FOLDER, filename)

    print(f"🔍 Generuotas kelias: {file_path}")
    print(f"🔍 Ar failas egzistuoja? {os.path.exists(file_path)}")

    if not os.path.exists(file_path):
        print(f"❌ Failas nerastas: {file_path}")
        return "Failas nerastas", 404

    print(f"✅ Failas rastas: {file_path}")
    return send_file(file_path, as_attachment=True)
