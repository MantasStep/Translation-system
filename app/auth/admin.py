# app/auth/admin.py

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, send_from_directory
)
from flask_login import login_required, current_user
from app import db
from app.database.models import User, TranslationMemory
import os

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

@admin_bp.route("/memory/download/<int:tm_id>/<which>")
def download_memory_file(tm_id, which):
    """
    which: 'original' arba 'translated'
    """
    tm = TranslationMemory.query.get_or_404(tm_id)

    # Įsitikiname, kad tai dokumentas
    if not tm.is_document or not tm.file_path:
        flash("Failas nerastas arba tai ne dokumentas", "warning")
        return redirect(url_for("admin.memory"))

    # Nustatome kurią versiją siųsti
    if which == "original":
        path = getattr(tm, "source_path", None) or tm.file_path
    else:
        path = tm.file_path

    if not os.path.exists(path):
        flash("Failas nerastas diske", "warning")
        return redirect(url_for("admin.memory"))

    folder, fname = os.path.split(path)
    return send_from_directory(
        directory=folder,
        path=fname,
        as_attachment=True,
        download_name=fname
    )
