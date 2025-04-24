from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson import json_util
import json
import time
from pymongo import MongoClient
import random

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['catclap_db']
collection = db['cats']

# Создаем Blueprint для маршрутов котов
cat_bp = Blueprint('cat_bp', __name__)

# Список имен для генерации случайных котов
cat_names = [
    "Шоколадка", "Джаз", "Смоки", "Янтарь", "Тень", "Чудо", "Муркотик", "Бублик", 
    "Персик", "Пушок", "Облачко", "Барсик", "Симба", "Леопольд", "Муся", "Масяня", 
    "Рыжик", "Марсик", "Снежок", "Кексик", "Пушинка", "Мурзик", "Черныш", "Васька"
]

# Окрас для генерации случайных котов
cat_colors = [
    "Коричневый", "Черно-белый", "Белый с серым", "Рыжий", "Черный", 
    "Трехцветный", "Серый", "Серо-белый", "Тигровый", "Черепаховый"
]

# Базовые описания для котов
cat_descriptions = [
    "Мягкий и пушистый котик, который очень любит ласку",
    "Котик с характером, но очень нежный с хозяином",
    "Уютный питомец, который станет вашим лучшим другом",
    "Независимый, но очень преданный, готов часами мурчать на коленях",
    "Игривый и активный, подарит вам море веселья",
    "Спокойный и умиротворенный, отлично подойдет для тихого дома",
    "Настоящий охотник, не пропустит ни одну мышь",
    "Общительный и дружелюбный, любит новых людей",
    "Немного застенчивый, но очень ласковый, когда привыкнет",
    "Любопытный исследователь, любит открывать новые территории"
]

# Получить всех котов
@cat_bp.route('/', methods=['GET'])
def get_cats():
    """Получить список всех котов"""
    limit = request.args.get('limit', 100, type=int)
    cats = list(collection.find().limit(limit))
    return json.loads(json_util.dumps(cats))

# Получить одного кота по ID
@cat_bp.route('/<id>', methods=['GET'])
def get_cat(id):
    """Получить кота по ID"""
    try:
        cat = collection.find_one({'_id': ObjectId(id)})
        if not cat:
            return {'error': 'Кот не найден'}, 404
        return json.loads(json_util.dumps(cat))
    except Exception as e:
        return {'error': str(e)}, 400

# Создать нового кота
@cat_bp.route('/', methods=['POST'])
def create_cat():
    """Создать нового кота"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    # Проверяем обязательные поля
    if 'name' not in data:
        return {'error': 'Имя кота обязательно'}, 400
    
    # Создаем нового кота
    cat = {
        'name': data.get('name'),
        'color': data.get('color', 'Неизвестно'),
        'bio': data.get('bio', 'Информация отсутствует'),
        'age': data.get('age', random.randint(1, 15)),
        'fish_count': data.get('fish_count', 0),
        'likes': data.get('likes', 0),
        'username': data.get('username', f"cat_{int(time.time())}"),
        'avatar': data.get('avatar', f"/cat_avatars/{random.randint(1, 10)}.jpg"),
        'lastInteractionTime': data.get('lastInteractionTime', int(time.time() * 1000)),
        'created_at': int(time.time())
    }
    
    result = collection.insert_one(cat)
    cat['_id'] = str(result.inserted_id)
    
    return json.loads(json_util.dumps(cat)), 201

# Обновить кота
@cat_bp.route('/<id>', methods=['PUT'])
def update_cat(id):
    """Обновить кота"""
    data = request.json
    if not data:
        return {'error': 'Данные не предоставлены'}, 400
    
    try:
        cat = collection.find_one({'_id': ObjectId(id)})
        if not cat:
            return {'error': 'Кот не найден'}, 404
        
        # Обновляем только разрешенные поля
        update_data = {}
        allowed_fields = ['name', 'color', 'bio', 'age', 'fish_count', 'likes', 'avatar', 'lastInteractionTime']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if update_data:
            collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        
        updated_cat = collection.find_one({'_id': ObjectId(id)})
        return json.loads(json_util.dumps(updated_cat))
    
    except Exception as e:
        return {'error': str(e)}, 400

# Удалить кота
@cat_bp.route('/<id>', methods=['DELETE'])
def delete_cat(id):
    """Удалить кота"""
    try:
        result = collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return {'error': 'Кот не найден'}, 404
        return {'message': 'Кот удален'}
    except Exception as e:
        return {'error': str(e)}, 400

# Поиск котов
@cat_bp.route('/search', methods=['GET'])
def search_cats():
    """Поиск котов по имени или username"""
    query = request.args.get('query', '').strip()
    if not query:
        return {'error': 'Поисковый запрос не предоставлен'}, 400
    
    try:
        # Поиск по имени или username с использованием регулярного выражения
        regex_query = {'$regex': query, '$options': 'i'}  # i для регистронезависимого поиска
        cats = list(collection.find({
            '$or': [
                {'name': regex_query},
                {'username': regex_query}
            ]
        }))
        
        return json.loads(json_util.dumps(cats))
    except Exception as e:
        return {'error': str(e)}, 400

# Модифицируем функцию generate_cats

@cat_bp.route('/generate', methods=['POST'])
def generate_cats():
    """Генерация котов для заполнения базы"""
    try:
        data = request.json
        if not data:
            return {'error': 'Данные не предоставлены'}, 400
        
        count = data.get('count', 10)
        custom_cats = data.get('customCats', [])
        
        generated_cats = []
        
        # Если предоставлены пользовательские коты, используем их
        if custom_cats:
            for cat_data in custom_cats:
                # Проверяем обязательные поля
                if 'name' not in cat_data:
                    cat_data['name'] = f"Котик {random.randint(100, 999)}"
                
                # Добавляем отладку для проверки данных
                print(f"Создаем кота: {cat_data['name']}")
                print(f"Bio: {cat_data.get('bio')}")
                print(f"Рarity: {cat_data.get('rarity')}")
                
                # Создаем кота с предоставленными данными
                cat = {
                    'name': cat_data.get('name'),
                    'color': cat_data.get('color', 'Неизвестно'),
                    'bio': cat_data.get('bio', 'Информация отсутствует'),
                    'store_description': cat_data.get('store_description', 'Этот котик ищет хозяина!'),
                    'age': cat_data.get('age', random.randint(1, 15)),
                    'fish_count': cat_data.get('fish_count', 0),
                    'likes': cat_data.get('likes', 0),
                    'price': cat_data.get('price', random.randint(50, 500)),
                    'rarity': cat_data.get('rarity', random.choice(['common', 'rare', 'legendary'])),
                    'username': cat_data.get('username', f"{cat_data.get('name', 'cat').lower()}_{random.randint(100, 999)}"),
                    'images': cat_data.get('images', {
                        'normal': f"/cat_avatars/normal/default.jpg",
                        'happy': f"/cat_avatars/happy/default.jpg",
                        'sad': f"/cat_avatars/sad/default.jpg"
                    }),
                    'lastInteractionTime': cat_data.get('lastInteractionTime', int(time.time() * 1000)),
                    'created_at': int(time.time())
                }
                
                result = collection.insert_one(cat)
                cat['_id'] = str(result.inserted_id)
                generated_cats.append(cat)
        else:
            # Если пользовательские коты не предоставлены, генерируем случайных котов
            for _ in range(count):
                cat_name = random.choice(cat_names)
                cat_color = random.choice(cat_colors)
                cat_bio = random.choice(cat_descriptions)
                
                cat = {
                    'name': f"{cat_name}",
                    'username': f"{cat_name.lower()}_{random.randint(100, 999)}",
                    'avatar': f"/cat_avatars/{random.randint(1, 10)}.jpg",
                    'bio': cat_bio,
                    'color': cat_color,
                    'age': random.randint(1, 15),
                    'fish_count': random.randint(0, 500),
                    'likes': random.randint(0, 100),
                    'price': random.randint(50, 300),
                    'rarity': random.choice(['common', 'rare', 'legendary']),
                    'lastInteractionTime': int(time.time() * 1000),
                    'images': {
                        'normal': f"/cat_avatars/normal/default.jpg",
                        'happy': f"/cat_avatars/happy/default.jpg",
                        'sad': f"/cat_avatars/sad/default.jpg"
                    },
                    'created_at': int(time.time())
                }
                
                result = collection.insert_one(cat)
                cat['_id'] = str(result.inserted_id)
                generated_cats.append(cat)
                
        # Возвращаем созданных котов
        return json.loads(json_util.dumps(generated_cats)), 201
            
    except Exception as e:
        print(f"Ошибка при генерации котов: {e}")
        return {'error': str(e)}, 400


# Получить случайного кота
@cat_bp.route('/random', methods=['GET'])
def get_random_cat():
    """Получить случайного кота"""
    try:
        # Получаем общее количество котов
        count = collection.count_documents({})
        if count == 0:
            return {'error': 'Нет доступных котов'}, 404
        
        # Выбираем случайного кота
        random_index = random.randint(0, count - 1)
        random_cat = list(collection.find().skip(random_index).limit(1))[0]
        
        return json.loads(json_util.dumps(random_cat))
    except Exception as e:
        return {'error': str(e)}, 400