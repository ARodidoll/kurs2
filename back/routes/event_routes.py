from flask import Blueprint, request, jsonify
from bson import ObjectId, json_util
import json
from config.database import get_database
from models.event import Event
from datetime import datetime

event_bp = Blueprint('event', __name__)
db = get_database()
collection = db['events']

@event_bp.route('/', methods=['GET'])
def get_events():
    """Получить список всех мероприятий"""
    events = list(collection.find())
    return json.loads(json_util.dumps(events))

@event_bp.route('/<id>', methods=['GET'])
def get_event(id):
    """Получить мероприятие по ID"""
    event = collection.find_one({'_id': ObjectId(id)})
    if not event:
        return {'error': 'Мероприятие не найдено'}, 404
    return json.loads(json_util.dumps(event))

@event_bp.route('/', methods=['POST'])
def create_event():
    """Создать новое мероприятие"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    # Преобразование строковых дат в datetime объекты
    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%dT%H:%M:%S') if data.get('start_date') else None
    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%dT%H:%M:%S') if data.get('end_date') else None
    
    event = Event(
        title=data.get('title'),
        description=data.get('description'),
        start_date=start_date,
        end_date=end_date,
        location=data.get('location'),
        max_participants=data.get('max_participants')
    )
    
    result = collection.insert_one(event.to_mongo())
    event._id = str(result.inserted_id)
    
    return json.loads(json_util.dumps(event.to_mongo())), 201

@event_bp.route('/<id>', methods=['PUT'])
def update_event(id):
    """Обновить мероприятие"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    # Проверяем существование записи
    if not collection.find_one({'_id': ObjectId(id)}):
        return {'error': 'Мероприятие не найдено'}, 404
    
    update_data = {}
    if 'title' in data:
        update_data['title'] = data['title']
    if 'description' in data:
        update_data['description'] = data['description']
    if 'start_date' in data:
        update_data['start_date'] = datetime.strptime(data['start_date'], '%Y-%m-%dT%H:%M:%S')
    if 'end_date' in data:
        update_data['end_date'] = datetime.strptime(data['end_date'], '%Y-%m-%dT%H:%M:%S')
    if 'location' in data:
        update_data['location'] = data['location']
    if 'max_participants' in data:
        update_data['max_participants'] = data['max_participants']
    
    collection.update_one(
        {'_id': ObjectId(id)},
        {'$set': update_data}
    )
    
    updated_event = collection.find_one({'_id': ObjectId(id)})
    return json.loads(json_util.dumps(updated_event))

@event_bp.route('/<id>', methods=['DELETE'])
def delete_event(id):
    """Удалить мероприятие"""
    result = collection.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return {'error': 'Мероприятие не найдено'}, 404
    return {'message': 'Мероприятие успешно удалено'}
