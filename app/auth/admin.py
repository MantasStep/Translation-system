# app/auth/admin.py

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, send_file
)
from flask_login import login_required, current_user
from app import db
from app.database.models import User, TranslationMemory
import os
from os.path import basename

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates/admin"
)

# --- Tik prisijungę adminai ---
@admin_bp.before_request
@login_required
def restrict_to_admin():
    if current_user.role.lower() != "admin":
        return "Neturi prieigos", 403

# --- Vartotojų skydelis ---
@admin_bp.route("/dashboard")
def dashboard():
    users = User.query.order_by(User.id).all()
    return render_template("dashboard.html", users=users)

@admin_bp.route("/create_user", methods=["POST"])
def create_user():
    username = request.form["username"].strip()
    pwd      = request.form["password"].strip()
    role     = request.form["role"].lower()

    u = User(username=username, role=role)
    u.set_password(pwd)
    # Užpildome abu DB laukus, jei jie egzistuoja:
    u.pwd_hash      = u.password_hash
    u.password_hash = u.password_hash

    db.session.add(u)
    db.session.commit()
    flash(f"Vartotojas “{username}” sukurtas", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/edit/<int:user_id>", methods=["GET","POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.username = request.form["username"].strip()
        user.role     = request.form["role"].lower()
        new_pwd = request.form["password"].strip()
        if new_pwd:
            user.set_password(new_pwd)
            user.pwd_hash      = user.password_hash
            user.password_hash = user.password_hash
        db.session.commit()
        flash(f"Vartotojas “{user.username}” atnaujintas", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("edit_user.html", user=user)

@admin_bp.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Negalima ištrinti savęs!", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"Vartotojas “{user.username}” ištrintas", "success")
    return redirect(url_for("admin.dashboard"))


# --- Translation Memory peržiūra ---
@admin_bp.route("/memory")
def memory():
    # Rikiuojame pagal ID (naujausi pirmi)
    records = TranslationMemory.query.order_by(
        TranslationMemory.id.desc()
    ).all()
    return render_template("memory.html", records=records)

@admin_bp.route('/download/<tm_id>/<which>', methods=['GET'])
def download_memory_file(tm_id, which):
    record = TranslationMemory.query.get(tm_id)
    
    if not record:
        return "Dokumentas nerastas", 404

    if which == 'original':
        filename = record.file_path
        # Paimame tik failo pavadinimą, jeigu kartais būtų pilnas kelias
        filename = basename(filename)
        file_path = os.path.join(r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\uploads", filename)
    elif which == 'translated':
        filename = record.translated_path
        
        if not filename.startswith("test_translated_"):
            filename = f"test_translated_{filename}"

        # Paimame tik failo pavadinimą, jeigu kartais būtų pilnas kelias
        filename = basename(filename)
        
        file_path = os.path.join(r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations", filename)
    else:
        return "Neteisingas kelias", 400
    
    print(f"🔍 Bandoma siųsti failą: {file_path}")
    if not os.path.exists(file_path):
        print(f"❌ Failas nerastas: {file_path}")
        print("Esami failai direktorijoje:")
        print(os.listdir(r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations"))
        return "Failas nerastas", 404

    return send_file(file_path, as_attachment=True)

