# app/translation/translate.py
import os
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from docx import Document
from app.translation.services.translation_service import TranslationService
from flask_login import login_required

translation_bp = Blueprint("translation", __name__,
                           template_folder="templates",
                           url_prefix="/translate")

svc = TranslationService()

@translation_bp.route("/", methods=["GET"])
@login_required
def translate_page():
    return render_template("translate.html")


@translation_bp.route("/", methods=["POST"])
@login_required
def translate_api():
    data = request.json
    result = svc.translate_api(data)
    return jsonify(result)


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

    # build safe filenames
    orig_name = uploaded.filename
    uid       = uuid.uuid4().hex
    base, ext = os.path.splitext(orig_name)

    # save original
    upl_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upl_dir, exist_ok=True)
    input_path = os.path.join(upl_dir, f"{uid}{ext}")
    uploaded.save(input_path)

    # prepare output path
    out_dir = current_app.config["TRANSLATED_FOLDER"]
    os.makedirs(out_dir, exist_ok=True)
    out_name = f"{base}_translated{ext}"
    output_path = os.path.join(out_dir, out_name)

    # if plain text → translate whole file at once
    if ext.lower() == ".txt":
        text = open(input_path, encoding="utf-8").read()
        best, _ = svc.translate_text(text, src, tgt)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(best)

    # if .docx → iterate paragraphs, preserve images automatically
    elif ext.lower() == ".docx":
        doc = Document(input_path)
        for p in doc.paragraphs:
            if p.text.strip():
                translated, _ = svc.translate_text(p.text, src, tgt)
                p.text = translated
        doc.save(output_path)

    else:
        return ("Nepalaikomas failo tipas", 400)

    # finally, return as download
    return send_file(
        output_path,
        as_attachment=True,
        download_name=out_name,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
            if ext.lower()==".docx" else "text/plain"
        )
    )
pass
