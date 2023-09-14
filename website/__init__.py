from flask import Flask
from os import path
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db_name='dapp'
db_user='root'
db_password=''
db_host='localhost'
BASE_URL='http://127.0.0.1/'

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask("__main__")
    app.config["SECRET_KEY"] = "gt"
    app.template_folder = "website/templates"
    app.static_folder = "website/static"
    print('name : {db_name}\n\n\n\n')

    

    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://{}:{}@{}/{}".format(db_user,db_password,db_host,db_name)

    db.init_app(app)

    @app.context_processor
    def global_variables():
        return {"BASE_URL":"http://127.0.0.1/"}

    from website.views import views
    from website.auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    create_database(app)

    from website.models import User

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app




def create_database(app):
    if not path.exists("website/" + DB_NAME):
        with app.app_context():
            db.create_all()
        print("Created Database!")
