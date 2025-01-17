import os

import stripe
from flask import Flask
from flask_socketio import SocketIO

import ai
import database
import lib.google as google

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["STRIPE_SECRET_KEY"] = os.environ.get("STRIPE_SECRET_KEY")
app.config["STRIPE_PUBLIC_KEY"] = os.environ.get("STRIPE_PUBLIC_KEY")
app.config["UPLOAD_FOLDER"] = "src/static/uploads"

app_debug = bool(app.config["DEBUG"])

# Initialize internal systems
ai.init(app)
database.init(app, local=app_debug)
google.init(app)

socketio = SocketIO(app, cors_allowed_origins="*")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Import routes into the main module
from api import *
from routes import *

if __name__ == "__main__":
    app.run()