from pymongo import MongoClient
import os

def get_database():
    """
    Функция для подключения к базе данных MongoDB
    """
    # Настройки подключения (можно вынести в переменные окружения)
    connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'alexandra_kursach')
    
    # Подключение к MongoDB
    client = MongoClient(connection_string)
    return client[db_name]
