class Config(object):
    SERVER_ADDRESS = '127.0.0.1:5000'
    DEBUG = True

    @staticmethod
    def init_app():
        pass


class DevelopmentConfig(Config):
    SECRET_KEY = 'd9030f835a1644cfa30e8f832b436c47'


class TestingConfig(Config):
    pass


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}