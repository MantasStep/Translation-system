__all__ = ['create_app', 'db', 'login']

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db    = SQLAlchemy()
login = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    # init extensions
    db.init_app(app)
    login.init_app(app)
    login.login_view = "auth.login"

    # upload/translations folders
    app.config['UPLOAD_FOLDER']     = os.path.join(app.instance_path, 'uploads')
    app.config['TRANSLATED_FOLDER'] = os.path.join(app.instance_path, 'translations')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TRANSLATED_FOLDER'], exist_ok=True)

    # import blueprints
    from app.auth.auth              import auth_bp
    from app.auth.admin             import admin_bp
    from app.translation.translate  import translation_bp

    # register blueprints *only once each*
    app.register_blueprint(auth_bp)                         # /login, /logout
    app.register_blueprint(admin_bp, url_prefix="/admin")   # /admin/dashboard, /admin/memory ...
    app.register_blueprint(translation_bp, url_prefix="/translate")

    return app
