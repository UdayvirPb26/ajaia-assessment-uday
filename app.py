import os
from flask import Flask, redirect, url_for
from extensions import db, login_manager
from models import User


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SECRET_KEY"] = "dev-secret-change-me"

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from routes.documents import docs_bp
    from routes.auth import auth_bp
    app.register_blueprint(docs_bp)
    app.register_blueprint(auth_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def home():
        return redirect(url_for("documents.list_documents"))

    with app.app_context():
        db.create_all()
        _seed_users()

    return app


def _seed_users():
    """Creates two demo accounts so reviewers/you can test the app immediately.
    alice / password123
    bob   / password123
    (Sharing between these two accounts will be wired up in Task 3.)
    """
    if User.query.count() == 0:
        alice = User(username="alice")
        alice.set_password("password123")
        bob = User(username="bob")
        bob.set_password("password123")
        db.session.add_all([alice, bob])
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
