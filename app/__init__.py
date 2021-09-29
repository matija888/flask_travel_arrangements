from flask import Flask

from config import config


def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    config[config_name].init_app()

    app.debug = app.config['DEBUG']
    app.secret_key = app.config['SECRET_KEY']

    with app.app_context():  # This makes config object available
        from .main import \
            main as main_blueprint  # These imports need to stay at the end of the function to prevent circular imports
        app.register_blueprint(main_blueprint)

    return app