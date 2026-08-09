from flask import Flask
from viewer.routes import viewer

def create_app():
    app = Flask(__name__)

    app.register_blueprint(viewer)

    return app