from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from model_training import train_model
from database import db
import os

task_routes = Blueprint('tasks', __name__, url_prefix='/api/v1')


@task_routes.route('/task', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    task_data = request.get_json()
    task_data['user_id'] = user_id
    task_data['creation_date'] = datetime.utcnow()
    task_data['status'] = 'created'
    try:
        result = db.insert_one('tasks', task_data)
        return jsonify({"message": "Task created successfully", "task_id": str(result.inserted_id)}), 201
    except DuplicateKeyError:
        return jsonify({"message": "Task already exists"}), 400

@task_routes.route('/task', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    tasks = list(db.find('tasks', {"user_id": user_id}))
    for task in tasks:
        task["_id"] = str(task["_id"])  # Convert ObjectID to string
    return jsonify(tasks), 200

@task_routes.route('/task/<task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    task = db.find_one_by_id('tasks', task_id)
    if task:
        task["_id"] = str(task["_id"])
        return jsonify(task), 200
    else:
        return jsonify({"message": "Task not found"}), 404

@task_routes.route('/task/<task_id>/train', methods=['POST'])
@jwt_required()
def train_task(task_id):
    user_id = get_jwt_identity()
    task = db.find_one_by_id('tasks', task_id)
    if task:
        model_info = train_model(task_id)
        model_info['task_id'] = task_id
        model_info['user_id'] = user_id
        model_info['time'] = datetime.utcnow()
        db.insert_one('models', model_info)
        return jsonify({"message": "Task model training initiated"}), 200
    else:
        return jsonify({"message": "Task not found"}), 404


@task_routes.route('/task/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    update_data = request.get_json()
    task = db.find_one_by_id('tasks', task_id)
    if task:
        db.update_one('tasks', task_id, update_data)
        return jsonify({"message": "Task updated successfully"}), 200
    else:
        return jsonify({"message": "Task not found"}), 404

@task_routes.route('/task/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task = db.find_one_by_id('tasks', task_id)
    if task:
        db.delete_one('tasks', task_id)
        return jsonify({"message": "Task deleted successfully"}), 200
    else:
        return jsonify({"message": "Task not found"}), 404
