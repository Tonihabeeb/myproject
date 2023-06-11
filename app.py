from flask import Flask, jsonify, json
from flask_jwt_extended import JWTManager
from bson import ObjectId
from dotenv import load_dotenv
import os
from flask_pymongo import PyMongo
from flask_cors import CORS
from database import get_db
from json import JSONEncoder
import json

load_dotenv()


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


def create_app():
    app = Flask(__name__)
    app.json_encoder = CustomJSONEncoder  # Add custom JSONEncoder here
    CORS(app)

    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    mongo = PyMongo(app)
    jwt = JWTManager(app)

    with app.app_context():
        db = get_db()  # Get the database connection here
        # Import your routes
        from user_routes import user_routes
        from task_routes import task_routes
        from file_routes import file_routes
        from websearch_routes import websearch_routes
        from ai_routes import ai_routes
        from file_export_routes import file_export_routes

        # Register your routes
        app.register_blueprint(user_routes, url_prefix='/api/users')
        app.register_blueprint(task_routes)
        app.register_blueprint(file_routes, url_prefix='/api/v1')
        app.register_blueprint(websearch_routes, url_prefix='/api/websearch')
        app.register_blueprint(ai_routes, url_prefix='/api/ai')
        app.register_blueprint(file_export_routes, url_prefix='/api/file_export')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
