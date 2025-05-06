# init_users.py
from datetime import datetime
from app import create_app, db
from app.database.models import User

app = create_app()
with app.app_context():
    # Išvalo esamas lenteles
    db.drop_all()
    db.create_all()

    # Paprastas vartotojas
    u = User(username="user", role="user", created_at=datetime.utcnow())
    u.set_password("user")
    # Jeigu set_password rašo į password_hash, perkelame tą reikšmę:
    u.pwd_hash = u.password_hash  
    db.session.add(u)

    # Admin
    a = User(username="admin", role="admin", created_at=datetime.utcnow())
    a.set_password("admin")
    a.pwd_hash = a.password_hash
    db.session.add(a)

    db.session.commit()
    print("Įrašyti vartotojai: user/user ir admin/admin")
