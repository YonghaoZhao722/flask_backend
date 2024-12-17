import os
from datetime import timedelta


class Config:
    DEBUG = True
    TESTING = True
    # 基础配置
    SECRET_KEY = 'dev'  # 开发环境使用简单的密钥
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'img')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # JWT配置
    JWT_ERROR_MESSAGE_KEY = "msg"
    JWT_SECRET_KEY = 'dev-jwt-key'  # 开发环境使用简单的JWT密钥
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=5, hours=12)

    # 数据库配置 - 使用简单的本地配置
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