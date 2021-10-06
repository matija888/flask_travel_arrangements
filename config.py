import os

class Config(object):
    SERVER_ADDRESS = '127.0.0.1:5000'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@127.0.0.1/travel_arrangements'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = 'd9030f835a1644cfa30e8f832b436c47'
    ITEM_PER_PAGE = 5

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


    @staticmethod
    def init_app():
        pass


class DevelopmentConfig(Config):
    LOGIN_DISABLED = False


class TestingConfig(Config):
    MAIL_SUPPRESS_SEND = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@127.0.0.1/test_travel_arrangements'
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    LOGIN_DISABLED = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}