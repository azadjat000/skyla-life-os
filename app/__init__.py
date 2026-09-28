from flask import Flask
from app.services.notification_service import start_notification_service
from config import Config
from .extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from .routes.main import main
    from .routes.finance import finance
    from .routes.finance_page import finance_page
    from .routes.pages import pages
    from .routes.core import core
    from .routes.motivation import motivation
    from .routes.discipline import discipline
    from .routes.obsession import obsession
    from .routes.football import football
    from .routes.sports import sports
    from .routes.football_skills import football_skills
    from .routes.fitness import fitness

    app.register_blueprint(main)
    app.register_blueprint(finance)
    app.register_blueprint(finance_page)
    app.register_blueprint(pages)
    app.register_blueprint(core)
    app.register_blueprint(motivation)
    app.register_blueprint(discipline)
    app.register_blueprint(obsession)
    app.register_blueprint(football)
    app.register_blueprint(sports)
    app.register_blueprint(football_skills)
    app.register_blueprint(fitness)

    with app.app_context():
        from . import models
        db.create_all()

    start_notification_service(app)

    return app
