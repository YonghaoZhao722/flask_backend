import os
from datetime import timedelta


class Config:
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'dev'  # Development environment uses simple keys
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'img')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    JWT_ERROR_MESSAGE_KEY = "msg"
    JWT_SECRET_KEY = 'dev-jwt-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=5, hours=12)

    SQLALCHEMY_DATABASE_URI = 'mysql://root:123321@localhost/social_media'
    CORS_SUPPORTS_CREDENTIALS = True

class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}