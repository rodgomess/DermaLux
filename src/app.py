
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()  # carrega .env
    app = Flask(__name__)

    # Blueprints
    from .routes.receive_message import receive_mensage_bp

    app.register_blueprint(receive_mensage_bp)

    return app