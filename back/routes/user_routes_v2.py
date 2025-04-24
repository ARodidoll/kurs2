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
users_collection = db['users']
donations_collection = db['donations']
transactions_collection = db['transactions']

# Создаем Blueprint для маршрутов пользователей
user_bp = Blueprint('user_bp', __name__)

# Создаем индексы при первом запуске
users_collection.create_index('user_id', unique=True)

def validate_user_id(user_id):
    """Проверяет, что ID пользователя имеет допустимый формат"""
    if user_id and isinstance(user_id, str) and (user_id.startswith('tg_') or user_id.startswith('web_')):
        return True
    return False

def get_or_create_user(user_id):
    """Получает пользователя или создает нового, если не существует"""
    if not validate_user_id(user_id):
        return None

    # Ищем пользователя по user_id
    user = users_collection.find_one({'user_id': user_id})
    
    # Если пользователь не найден, создаем нового
    if not user:
        new_user = {
            'user_id': user_id,
            'nickname': f'User_{user_id[-6:]}',
            'username': f'user_{user_id[-6:]}',
            'coins_count': 0,
            'claps_count': 0,
            'friends': [],
            'mood': 'normal',
            'lastInteractionTime': int(time.time() * 1000),
            'created_at': int(time.time())
        }
        result = users_collection.insert_one(new_user)
        new_user['_id'] = str(result.inserted_id)
        return new_user
    
    return user

# Получить всех пользователей
@user_bp.route('/', methods=['GET'])
def get_users():
    """Получить список всех пользователей"""
    limit = request.args.get('limit', 100, type=int)
    users = list(users_collection.find().limit(limit))
    return json.loads(json_util.dumps(users))

# Получить одного пользователя по ID
@user_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Получить пользователя по ID"""
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        # Получаем или создаем пользователя
        user = get_or_create_user(user_id)
        
        if not user:
            return {'error': 'Пользователь не найден или не может быть создан'}, 404
            
        return json.loads(json_util.dumps(user))
    except Exception as e:
        return {'error': str(e)}, 500

# Создать нового пользователя
@user_bp.route('/', methods=['POST'])
def create_user():
    """Создать нового пользователя"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    user_id = data.get('user_id')
    if not validate_user_id(user_id):
        return {'error': 'Неверный формат ID пользователя'}, 400
    
    # Проверяем, существует ли пользователь
    existing_user = users_collection.find_one({'user_id': user_id})
    if existing_user:
        return {'error': 'Пользователь с таким ID уже существует'}, 409
    
    user = {
        'user_id': user_id,
        'nickname': data.get('nickname', f'User_{user_id[-6:]}'),
        'username': data.get('username', f'user_{user_id[-6:]}'),
        'coins_count': data.get('coins_count', 0),
        'claps_count': data.get('claps_count', 0),
        'cat': data.get('cat'),
        'friends': data.get('friends', []),
        'mood': data.get('mood', 'normal'),
        'lastInteractionTime': data.get('lastInteractionTime', int(time.time() * 1000)),
        'created_at': int(time.time())
    }
    
    result = users_collection.insert_one(user)
    user['_id'] = str(result.inserted_id)
    
    return json.loads(json_util.dumps(user)), 201

# Обновить пользователя
@user_bp.route('/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Обновить пользователя"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        user = users_collection.find_one({'user_id': user_id})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        # Если в запросе есть данные по добавлению/удалению друга
        if 'friend' in data:
            friend_data = data['friend']
            friend_id = friend_data.get('id')
            action = friend_data.get('action')
            
            if action == 'add':
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$addToSet': {'friends': friend_id}}
                )
            elif action == 'remove':
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$pull': {'friends': friend_id}}
                )
            
            # Удаляем обработанные данные о друге
            del data['friend']
        
        # Обновляем остальные поля пользователя
        update_data = {}
        for key, value in data.items():
            if key != '_id' and key != 'user_id':  # Пропускаем попытку изменить ID
                update_data[key] = value
        
        if update_data:
            users_collection.update_one({'user_id': user_id}, {'$set': update_data})
        
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    
    except Exception as e:
        return {'error': str(e)}, 500

# Удалить пользователя
@user_bp.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Удалить пользователя"""
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        result = users_collection.delete_one({'user_id': user_id})
        if result.deleted_count == 0:
            return {'error': 'Пользователь не найден'}, 404
        return {'message': 'Пользователь удален'}
    except Exception as e:
        return {'error': str(e)}, 500

# Получить список друзей пользователя
@user_bp.route('/<user_id>/friends', methods=['GET'])
def get_user_friends(user_id):
    """Получить список друзей пользователя"""
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        # Получаем или создаем пользователя
        user = get_or_create_user(user_id)
        if not user:
            return {'error': 'Пользователь не найден или не может быть создан'}, 404
        
        friend_ids = user.get('friends', [])
        friends = []
        
        for friend_id in friend_ids:
            if validate_user_id(friend_id):
                friend = users_collection.find_one({'user_id': friend_id})
                if friend:
                    friends.append(friend)
        
        return json.loads(json_util.dumps(friends))
    except Exception as e:
        return {'error': str(e)}, 500

# Добавить пользователя в друзья
@user_bp.route('/<user_id>/friends/<friend_id>', methods=['POST'])
def add_friend(user_id, friend_id):
    """Добавить пользователя в друзья"""
    try:
        if not validate_user_id(user_id) or not validate_user_id(friend_id):
            return {'error': 'Неверный формат ID пользователя или друга'}, 400
        
        # Проверяем существование обоих пользователей
        user = get_or_create_user(user_id)
        friend = get_or_create_user(friend_id)
        
        if not user or not friend:
            return {'error': 'Пользователь или друг не найден или не может быть создан'}, 404
        
        # Добавляем друга пользователю
        users_collection.update_one(
            {'user_id': user_id},
            {'$addToSet': {'friends': friend_id}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 500

# Удалить пользователя из друзей
@user_bp.route('/<user_id>/friends/<friend_id>', methods=['DELETE'])
def remove_friend(user_id, friend_id):
    """Удалить пользователя из друзей"""
    try:
        if not validate_user_id(user_id) or not validate_user_id(friend_id):
            return {'error': 'Неверный формат ID пользователя или друга'}, 400
        
        # Проверяем существование пользователя
        user = users_collection.find_one({'user_id': user_id})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        # Удаляем друга у пользователя
        users_collection.update_one(
            {'user_id': user_id},
            {'$pull': {'friends': friend_id}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 500

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
    
    top_users = list(users_collection.aggregate(pipeline))
    return json.loads(json_util.dumps(top_users))

# Покупка валюты
@user_bp.route('/<user_id>/purchase', methods=['POST'])
def purchase_currency(user_id):
    """Покупка валюты"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        # Получаем или создаем пользователя
        user = get_or_create_user(user_id)
        if not user:
            return {'error': 'Пользователь не найден или не может быть создан'}, 404
        
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
        
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': update_field}
        )
        
        # Записываем транзакцию
        transaction = {
            'user_id': user_id,
            'type': 'purchase',
            'currency_type': currency_type,
            'amount': amount,
            'timestamp': int(time.time())
        }
        transactions_collection.insert_one(transaction)
        
        # Возвращаем обновленного пользователя
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 500

# Сделать донат
@user_bp.route('/<user_id>/donate', methods=['POST'])
def donate(user_id):
    """Сделать донат"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        user = users_collection.find_one({'user_id': user_id})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return {'error': 'Сумма доната должна быть положительной'}, 400
        
        # Проверяем, достаточно ли у пользователя монет
        if user.get('coins_count', 0) < amount:
            return {'error': 'Недостаточно монет для доната'}, 400
        
        # Вычитаем монеты у пользователя
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'coins_count': -amount}}
        )
        
        # Записываем донат
        donation = {
            'user_id': user_id,
            'amount': amount,
            'timestamp': int(time.time()),
            'donation_type': 'shelter'
        }
        donations_collection.insert_one(donation)
        
        # Возвращаем обновленного пользователя
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 500

# Обновить настроение кота
@user_bp.route('/<user_id>/mood', methods=['POST'])
def update_mood(user_id):
    """Обновить настроение кота"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        user = users_collection.find_one({'user_id': user_id})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        mood = data.get('mood')
        if not mood:
            return {'error': 'Настроение не указано'}, 400
        
        # Обновляем настроение
        users_collection.update_one(
            {'user_id': user_id},
            {'$set': {'mood': mood}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 500

# Обновить время последнего взаимодействия
@user_bp.route('/<user_id>/interaction', methods=['POST'])
def update_interaction_time(user_id):
    """Обновить время последнего взаимодействия"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        if not validate_user_id(user_id):
            return {'error': 'Неверный формат ID пользователя'}, 400
        
        user = users_collection.find_one({'user_id': user_id})
        if not user:
            return {'error': 'Пользователь не найден'}, 404
        
        timestamp = data.get('timestamp', int(time.time() * 1000))
        
        # Обновляем время взаимодействия
        users_collection.update_one(
            {'user_id': user_id},
            {'$set': {'lastInteractionTime': timestamp}}
        )
        
        # Возвращаем обновленного пользователя
        updated_user = users_collection.find_one({'user_id': user_id})
        return json.loads(json_util.dumps(updated_user))
    except Exception as e:
        return {'error': str(e)}, 500