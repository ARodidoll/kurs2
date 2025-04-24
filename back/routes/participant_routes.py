from flask import Blueprint, request, jsonify
from bson import ObjectId, json_util
import json
from config.database import get_database
from models.participant import Participant

participant_bp = Blueprint('participant', __name__)
db = get_database()
collection = db['participants']

@participant_bp.route('/', methods=['GET'])
def get_participants():
    """Получить список всех участников"""
    participants = list(collection.find())
    return json.loads(json_util.dumps(participants))

@participant_bp.route('/<id>', methods=['GET'])
def get_participant(id):
    """Получить участника по ID"""
    participant = collection.find_one({'_id': ObjectId(id)})
    if not participant:
        return {'error': 'Участник не найден'}, 404
    return json.loads(json_util.dumps(participant))

@participant_bp.route('/', methods=['POST'])
def create_participant():
    """Создать нового участника"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    participant = Participant(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        events=data.get('events', [])
    )
    
    result = collection.insert_one(participant.to_mongo())
    participant._id = str(result.inserted_id)
    
    return json.loads(json_util.dumps(participant.to_mongo())), 201

@participant_bp.route('/<id>', methods=['PUT'])
def update_participant(id):
    """Обновить участника"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    # Проверяем существование записи
    if not collection.find_one({'_id': ObjectId(id)}):
        return {'error': 'Участник не найден'}, 404
    
    update_data = {}
    if 'name' in data:
        update_data['name'] = data['name']
    if 'email' in data:
        update_data['email'] = data['email']
    if 'phone' in data:
        update_data['phone'] = data['phone']
    if 'events' in data:
        update_data['events'] = data['events']
    
    collection.update_one(
        {'_id': ObjectId(id)},
        {'$set': update_data}
    )
    
    updated_participant = collection.find_one({'_id': ObjectId(id)})
    return json.loads(json_util.dumps(updated_participant))

@participant_bp.route('/<id>', methods=['DELETE'])
def delete_participant(id):
    """Удалить участника"""
    result = collection.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return {'error': 'Участник не найден'}, 404
    return {'message': 'Участник успешно удален'}
