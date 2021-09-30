class Config(object):
    SERVER_ADDRESS = '127.0.0.1:5000'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@127.0.0.1/travel_arrangements'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = 'd9030f835a1644cfa30e8f832b436c47'

    @staticmethod
    def init_app():
        pass


class DevelopmentConfig(Config):
    pass


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@127.0.0.1/test_travel_arrangements'
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}