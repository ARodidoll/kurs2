from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson import json_util
import json
import time
from pymongo import MongoClient
from datetime import datetime, timedelta

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['catclap_db']
collection = db['users']
donations_collection = db['donations']

# Создаем Blueprint для маршрутов пользователей
user_bp = Blueprint('user_bp', __name__)

# Получить всех пользователей
@user_bp.route('/', methods=['GET'])
def get_users():
    """Получить список всех пользователей"""
    limit = request.args.get('limit', 100, type=int)
    users = list(collection.find().limit(limit))
    return json.loads(json_util.dumps(users))

# Получить одного пользователя по ID
@user_bp.route('/<id>', methods=['GET'])
def get_user(id):
    """Получить пользователя по ID"""
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        return json.loads(json_util.dumps(user))
    except Exception as e:
        return {'error': str(e)}, 400

# Создать нового пользователя
@user_bp.route('/', methods=['POST'])
def create_user():
    """Создать нового пользователя"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    user = {
        'nickname': data.get('nickname', 'Гость'),
        'username': data.get('username', f'guest_{int(time.time())}'),
        'coins_count': data.get('coins_count', 0),
        'claps_count': data.get('claps_count', 0),
        'cat': data.get('cat'),
        'friends': data.get('friends', []),
        'mood': data.get('mood', 'normal'),
        'lastInteractionTime': data.get('lastInteractionTime', int(time.time() * 1000)),
        'created_at': int(time.time())
    }
    
    result = collection.insert_one(user)
    user['_id'] = str(result.inserted_id)
    
    return json.loads(json_util.dumps(user)), 201

# Обновить пользователя
@user_bp.route('/<id>', methods=['PUT'])
def update_user(id):
    """Обновить пользователя"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        # Если в запросе есть данные по добавлению/удалению друга
        if 'friend' in data:
            friend_data = data['friend']
            friend_id = friend_data.get('id')
            action = friend_data.get('action')
            
            if action == 'add':
                collection.update_one(
                    {'_id': ObjectId(id)},
                    {'$addToSet': {'friends': friend_id}}
                )
            elif action == 'remove':
                collection.update_one(
                    {'_id': ObjectId(id)},
                    {'$pull': {'friends': friend_id}}
                )
            
            # Удаляем обработанные данные о друге
            del data['friend']
        
        # Обновляем остальные поля пользователя
        update_data = {}
        for key, value in data.items():
            if key != '_id':  # Пропускаем попытку изменить ID
                update_data[key] = value
        
        if update_data:
            collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    
    except Exception as e:
        return {'error': str(e)}, 400

# Удалить пользователя
@user_bp.route('/<id>', methods=['DELETE'])
def delete_user(id):
    """Удалить пользователя"""
    try:
        result = collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return {'error': 'Пользователь не найден'}, 404
        return {'message': 'Пользователь удален'}
    except Exception as e:
        return {'error': str(e)}, 400

# Получить список друзей пользователя
@user_bp.route('/<id>/friends', methods=['GET'])
def get_user_friends(id):
    """Получить список друзей пользователя"""
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        friend_ids = user.get('friends', [])
        friends = []
        
        for friend_id in friend_ids:
            try:
                friend = collection.find_one({'_id': ObjectId(friend_id)})
                if friend:
                    friends.append(friend)
            except:
                # Пропускаем невалидные ID
                pass
        
        return json.loads(json_util.dumps(friends))
    except Exception as e:
        return {'error': str(e)}, 400

# Добавить пользователя в друзья
@user_bp.route('/<id>/friends/<friend_id>', methods=['POST'])
def add_friend(id, friend_id):
    """Добавить пользователя в друзья"""
    try:
        # Проверяем существование обоих пользователей
        user = collection.find_one({'_id': ObjectId(id)})
        friend = collection.find_one({'_id': ObjectId(friend_id)})
        
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        if not friend:
            return {'error': 'Друг не найден'}, 404
        
        # Добавляем друга пользователю
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$addToSet': {'friends': friend_id}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 400

# Удалить пользователя из друзей
@user_bp.route('/<id>/friends/<friend_id>', methods=['DELETE'])
def remove_friend(id, friend_id):
    """Удалить пользователя из друзей"""
    try:
        # Проверяем существование пользователя
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        # Удаляем друга у пользователя
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$pull': {'friends': friend_id}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 400

# Получить топ пользователей
@user_bp.route('/top', methods=['GET'])
def get_top_users():
    """Получить топ пользователей"""
    period = request.args.get('period', 'day')
    
    # Определяем временные рамки в зависимости от периода
    now = datetime.now()
    if period == 'day':
        start_time = int((now - timedelta(days=1)).timestamp())
    elif period == 'week':
        start_time = int((now - timedelta(weeks=1)).timestamp())
    elif period == 'month':
        start_time = int((now - timedelta(days=30)).timestamp())
    else:
        start_time = 0
    
    # Формируем запрос в зависимости от периода
    pipeline = [
        {'$match': {'created_at': {'$gte': start_time}}},
        {'$sort': {'coins_count': -1}},
        {'$limit': 20}
    ]
    
    top_users = list(collection.aggregate(pipeline))
    return json.loads(json_util.dumps(top_users))

# Покупка валюты
@user_bp.route('/<id>/purchase', methods=['POST'])
def purchase_currency(id):
    """Покупка валюты"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        currency_type = data.get('type')
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return {'error': 'Количество должно быть положительным'}, 400
        
        # Обновляем соответствующий счетчик валюты
        update_field = {}
        if currency_type == 'coins':
            update_field = {'coins_count': amount}
        elif currency_type == 'claps':
            update_field = {'claps_count': amount}
        else:
            return {'error': 'Неверный тип валюты'}, 400
        
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$inc': update_field}
        )
        
        # Записываем транзакцию (опционально)
        transaction = {
            'user_id': id,
            'type': 'purchase',
            'currency_type': currency_type,
            'amount': amount,
            'timestamp': int(time.time())
        }
        db['transactions'].insert_one(transaction)
        
        # Возвращаем обновленного пользователя
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 400

# Сделать донат
@user_bp.route('/<id>/donate', methods=['POST'])
def donate(id):
    """Сделать донат"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return {'error': 'Сумма доната должна быть положительной'}, 400
        
        # Проверяем, достаточно ли у пользователя монет
        if user.get('coins_count', 0) < amount:
            return {'error': 'Недостаточно монет для доната'}, 400
        
        # Вычитаем монеты у пользователя
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$inc': {'coins_count': -amount}}
        )
        
        # Записываем донат
        donation = {
            'user_id': id,
            'amount': amount,
            'timestamp': int(time.time()),
            'donation_type': 'shelter'
        }
        donations_collection.insert_one(donation)
        
        # Возвращаем обновленного пользователя
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 400

# Обновить настроение кота
@user_bp.route('/<id>/mood', methods=['POST'])
def update_mood(id):
    """Обновить настроение кота"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        mood = data.get('mood')
        if not mood:
            return {'error': 'Настроение не указано'}, 400
        
        # Обновляем настроение
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'mood': mood}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 400

# Обновить время последнего взаимодействия
@user_bp.route('/<id>/interaction', methods=['POST'])
def update_interaction_time(id):
    """Обновить время последнего взаимодействия"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        user = collection.find_one({'_id': ObjectId(id)})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        timestamp = data.get('timestamp', int(time.time() * 1000))
        
        # Обновляем время взаимодействия
        collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'lastInteractionTime': timestamp}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 400