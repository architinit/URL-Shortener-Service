from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
