import pymysql
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
from config import config
from logging_config import setup_logging

pymysql.install_as_MySQLdb()

# Instantiate Extension
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config[config_name])

    # Setup Logging
    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
    setup_logging(log_file)

    # Initialize Extension
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

    # Register Blueprint
    from .routes.user import user_bp
    from .routes.post import post_bp
    from .routes.comment import comment_bp
    from .routes.independent_routes import independent_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(post_bp, url_prefix='/post')
    app.register_blueprint(comment_bp, url_prefix='/comment')
    app.register_blueprint(independent_bp)

    # Create an upload directory
    for dir_name in ['avatar', 'post']:
        path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
        if not os.path.exists(path):
            os.makedirs(path)

    return app