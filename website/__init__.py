from flask import Flask
from os import path
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():

    app = Flask('__main__')
    app.config['SECRET_KEY'] = 'gt'
    app.template_folder = 'website/templates'
    app.static_folder = 'website/static'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/dapp'

    db.init_app(app)

    from website.views import views
    from website.auth import auth
    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    create_database(app)

    from website.models import User

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    if not path.exists('website/'+DB_NAME):
        with app.app_context():
            db.create_all()
        print("Created Database!")
