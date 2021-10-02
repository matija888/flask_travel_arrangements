from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from config import config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    config[config_name].init_app()

    app.debug = app.config['DEBUG']
    app.secret_key = app.config['SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():  # This makes config object available
        from .main import \
            main as main_blueprint  # These imports need to stay at the end of the function to prevent circular imports
        app.register_blueprint(main_blueprint)

        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app