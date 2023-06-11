from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import get_db
import os

load_dotenv()

jwt_secret_key = os.getenv('JWT_SECRET_KEY')

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/register', methods=['POST'])
def register():
    db = get_db()
    users = db.db.users  # changed this line
    username = request.get_json()['username']
    password = request.get_json()['password']
    hashed_password = generate_password_hash(password)

    user_id = users.insert_one({
        'username': username,
        'password': hashed_password
    }).inserted_id

    result = {
        'username': username,
        'password': hashed_password,
        'id': str(user_id)
    }

    return jsonify({'result': result})

@user_routes.route('/login', methods=['POST'])
def login():
    db = get_db()  # added this line
    users = db.db.users  # changed this line
    username = request.get_json()['username']
    password = request.get_json()['password']
    result = ""

    response = users.find_one({'username': username})

    if response:
        if check_password_hash(response['password'], password):
            access_token = create_access_token(identity = {
                'username': response['username'],
                'id': str(response['_id'])
            })
            result = jsonify({'token': access_token})
        else:
            result = jsonify({'error': 'Invalid username and password'})
    else:
        result = jsonify({'result': 'No results found'})

    return result
