from flask import Flask, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from flask_migrate import Migrate

# 实例化扩展
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app,
         resources={r"/*": {
             "origins": ["http://localhost:5173"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }})

    # 注册蓝图
    from .routes.user import user_bp
    from .routes.post import post_bp
    from .routes.comment import comment_bp
    from .routes.independent_routes import independent_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(post_bp, url_prefix='/post')
    app.register_blueprint(comment_bp, url_prefix='/comment')
    app.register_blueprint(independent_bp)
    # 创建上传目录

    import os
    for dir_name in ['avatar', 'post']:
        path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
        if not os.path.exists(path):
            os.makedirs(path)


    return app