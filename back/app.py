from flask import Flask, jsonify,send_from_directory
from flask_cors import CORS
from routes.user_routes_v2 import user_bp
from routes.cat_routes import cat_bp
from routes.stats_routes import stats_bp
import os
from pymongo import MongoClient
import time

app = Flask(__name__)
CORS(app)  # Включение Cross-Origin Resource Sharing для работы с фронтендом

# Регистрация blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(cat_bp, url_prefix='/api/cats')
app.register_blueprint(stats_bp, url_prefix='/api/stats')

# Обработчик для статических файлов вне папки static
@app.route('/cat_avatars/<path:filename>')
def custom_static(filename):
    print(f"Запрос файла: {filename}")  # Добавим логирование для отладки
    try:
        return send_from_directory('static/cat_avatars', filename)
    except Exception as e:
        print(f"Ошибка доступа к файлу {filename}: {e}")
        return "Файл не найден", 404
      
# Проверка соединения с MongoDB при запуске
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['catclap_db']
    # Проверяем соединение
    client.server_info()
    print("Успешное подключение к MongoDB")
    
    # Инициализация базовых данных, если необходимо
    if db['users'].count_documents({}) == 0:
        print("Создание тестового пользователя...")
        db['users'].insert_one({
            'nickname': 'Тестовый кот',
            'username': 'test_cat',
            'coins_count': 100,
            'claps_count': 50,
            'mood': 'normal',
            'lastInteractionTime': int(time.time() * 1000),
            'created_at': int(time.time())
        })
    
    if db['shelters'].count_documents({}) == 0:
        print("Создание тестового приюта...")
        db['shelters'].insert_one({
            'name': 'Котодом',
            'address': 'г. Москва, ул. Примерная, 123',
            'description': 'Приют для бездомных котиков',
            'website': 'https://kotodom.ru',
            'created_at': int(time.time())
        })
        
except Exception as e:
    print(f"Ошибка подключения к MongoDB: {e}")

# Обработчик корневого маршрута
@app.route('/')
def index():
    return jsonify({
        'status': 'success',
        'message': 'CatClap API работает!'
    })

# Обработчик ошибок
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ресурс не найден'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)