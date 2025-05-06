# norint pasileist koda:
# venv\Scripts\activate
# python -m flask run

# i gita koda pushint:
# git add .
# git commit -m "pavadinimas"
# git push

from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app = create_app()
    with app.test_request_context():
        print("Available routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint:30s} -> {rule}")
    app.run(debug=True)
