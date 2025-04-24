from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson import json_util
import json
import time
from datetime import datetime, timedelta
from pymongo import MongoClient

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['catclap_db']
donations_collection = db['donations']
users_collection = db['users']
shelters_collection = db['shelters']
cats_collection = db['cats']

# Создаем Blueprint для маршрутов статистики
stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/donations', methods=['GET'])
def get_donation_stats():
    """Получить статистику по донатам"""
    try:
        # Всего собрано средств (всё время)
        total_donations = sum(donation.get('amount', 0) for donation in donations_collection.find())
        
        # Количество спасенных котиков (примерная формула)
        # Например, 1 спасенный кот = 1000 рублей пожертвований
        saved_cats = total_donations // 1000
        
        # Количество приютов-партнеров
        shelter_partners = shelters_collection.count_documents({})
        if shelter_partners == 0:
            # Если приютов нет в базе, устанавливаем минимум 1
            shelter_partners = 1
        
        # Статистика для текущего месяца
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_month = int(current_month.timestamp())
        
        # Сумма пожертвований за текущий месяц
        current_month_donations = sum(
            donation.get('amount', 0) 
            for donation in donations_collection.find({'timestamp': {'$gte': start_of_month}})
        )
        
        # Цель на месяц (статично или из базы)
        monthly_goal = 10000  # 10000 рублей
        
        # Собираем данные за последние 30 дней
        days_data = []
        today = datetime.now()
        
        for i in range(30, -1, -1):
            day_date = today - timedelta(days=i)
            day_start = int(day_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            day_end = int(day_date.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())
            
            day_donations = sum(
                donation.get('amount', 0) 
                for donation in donations_collection.find({
                    'timestamp': {
                        '$gte': day_start, 
                        '$lte': day_end
                    }
                })
            )
            
            days_data.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'amount': day_donations
            })
        
        response_data = {
            'savedCats': saved_cats,
            'totalDonations': total_donations,
            'shelterPartners': shelter_partners,
            'currentMonthAmount': current_month_donations,
            'monthlyGoal': monthly_goal,
            'daysData': days_data
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return {'error': str(e)}, 500

@stats_bp.route('/users', methods=['GET'])
def get_user_stats():
    """Получить статистику по пользователям"""
    try:
        # Общее количество пользователей
        total_users = users_collection.count_documents({})
        
        # Новые пользователи за последние 24 часа
        yesterday = int((datetime.now() - timedelta(days=1)).timestamp())
        new_users_24h = users_collection.count_documents({'created_at': {'$gte': yesterday}})
        
        # Активные пользователи (были активны за последние 7 дней)
        week_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        active_users = users_collection.count_documents({'lastInteractionTime': {'$gte': week_ago * 1000}})
        
        # Статистика верхнего уровня по монетам и хлопкам
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'totalCoins': {'$sum': '$coins_count'},
                    'totalClaps': {'$sum': '$claps_count'},
                    'avgCoins': {'$avg': '$coins_count'},
                    'avgClaps': {'$avg': '$claps_count'}
                }
            }
        ]
        
        currency_stats = list(users_collection.aggregate(pipeline))
        
        response_data = {
            'totalUsers': total_users,
            'newUsers24h': new_users_24h,
            'activeUsers': active_users
        }
        
        # Добавляем статистику валюты, если есть результаты
        if currency_stats and len(currency_stats) > 0:
            response_data.update({
                'totalCoins': currency_stats[0].get('totalCoins', 0),
                'totalClaps': currency_stats[0].get('totalClaps', 0),
                'avgCoins': currency_stats[0].get('avgCoins', 0),
                'avgClaps': currency_stats[0].get('avgClaps', 0)
            })
        
        return jsonify(response_data)
    
    except Exception as e:
        return {'error': str(e)}, 500

@stats_bp.route('/top/day', methods=['GET'])
def get_top_day():
    """Получить топ пользователей за день"""
    try:
        # Начало текущего дня
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_day = int(today.timestamp())
        
        # Получаем донаты за день
        day_donations = list(donations_collection.find({'timestamp': {'$gte': start_of_day}}))
        
        # Группируем донаты по пользователям
        user_donations = {}
        for donation in day_donations:
            user_id = donation.get('user_id')
            amount = donation.get('amount', 0)
            
            if user_id not in user_donations:
                user_donations[user_id] = {'amount': 0, 'count': 0}
            
            user_donations[user_id]['amount'] += amount
            user_donations[user_id]['count'] += 1
        
        # Получаем информацию о пользователях
        top_users = []
        for user_id, stats in user_donations.items():
            try:
                user = users_collection.find_one({'_id': ObjectId(user_id)})
                if user:
                    top_users.append({
                        'id': str(user['_id']),
                        'name': user.get('nickname', 'Гость'),
                        'telegram': user.get('username', 'unknown'),
                        'avatar': user.get('avatar', '/default-cat-avatar.png'),
                        'isOnline': (datetime.now().timestamp() - user.get('lastInteractionTime', 0) / 1000) < 3600,
                        'amount': stats['amount'],
                        'count': stats['count'],
                        'trend': 0  # Для дневной статистики тренд всегда 0
                    })
            except Exception:
                continue
        
        # Сортируем по сумме донатов
        top_users.sort(key=lambda x: x['amount'], reverse=True)
        
        return jsonify(top_users)
    
    except Exception as e:
        return {'error': str(e)}, 500

@stats_bp.route('/top/week', methods=['GET'])
def get_top_week():
    """Получить топ пользователей за неделю"""
    try:
        # Начало текущей недели
        today = datetime.now()
        start_of_week = int((today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0).timestamp())
        
        # Получаем донаты за неделю
        week_donations = list(donations_collection.find({'timestamp': {'$gte': start_of_week}}))
        
        # Группируем донаты по пользователям
        user_donations = {}
        for donation in week_donations:
            user_id = donation.get('user_id')
            amount = donation.get('amount', 0)
            
            if user_id not in user_donations:
                user_donations[user_id] = {'amount': 0, 'count': 0}
            
            user_donations[user_id]['amount'] += amount
            user_donations[user_id]['count'] += 1
        
        # Получаем также донаты за предыдущую неделю для тренда
        prev_week_start = int((today - timedelta(days=today.weekday() + 7)).replace(
            hour=0, minute=0, second=0, microsecond=0).timestamp())
        prev_week_end = start_of_week - 1
        
        prev_week_donations = list(donations_collection.find({
            'timestamp': {'$gte': prev_week_start, '$lte': prev_week_end}
        }))
        
        # Группируем донаты за предыдущую неделю
        prev_user_donations = {}
        for donation in prev_week_donations:
            user_id = donation.get('user_id')
            amount = donation.get('amount', 0)
            
            if user_id not in prev_user_donations:
                prev_user_donations[user_id] = {'amount': 0}
            
            prev_user_donations[user_id]['amount'] += amount
        
        # Получаем информацию о пользователях
        top_users = []
        for user_id, stats in user_donations.items():
            try:
                user = users_collection.find_one({'_id': ObjectId(user_id)})
                if user:
                    # Рассчитываем тренд
                    prev_amount = prev_user_donations.get(user_id, {}).get('amount', 0)
                    trend = 0
                    if prev_amount > 0:
                        trend = int(((stats['amount'] - prev_amount) / prev_amount) * 100)
                    
                    top_users.append({
                        'id': str(user['_id']),
                        'name': user.get('nickname', 'Гость'),
                        'telegram': user.get('username', 'unknown'),
                        'avatar': user.get('avatar', '/default-cat-avatar.png'),
                        'isOnline': (datetime.now().timestamp() - user.get('lastInteractionTime', 0) / 1000) < 3600,
                        'amount': stats['amount'],
                        'count': stats['count'],
                        'trend': trend
                    })
            except Exception:
                continue
        
        # Сортируем по сумме донатов
        top_users.sort(key=lambda x: x['amount'], reverse=True)
        
        return jsonify(top_users)
    
    except Exception as e:
        return {'error': str(e)}, 500

@stats_bp.route('/top/month', methods=['GET'])
def get_top_month():
    """Получить топ пользователей за месяц"""
    try:
        # Начало текущего месяца
        today = datetime.now()
        start_of_month = int(today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0).timestamp())
        
        # Получаем донаты за месяц
        month_donations = list(donations_collection.find({'timestamp': {'$gte': start_of_month}}))
        
        # Группируем донаты по пользователям
        user_donations = {}
        for donation in month_donations:
            user_id = donation.get('user_id')
            amount = donation.get('amount', 0)
            
            if user_id not in user_donations:
                user_donations[user_id] = {'amount': 0, 'count': 0}
            
            user_donations[user_id]['amount'] += amount
            user_donations[user_id]['count'] += 1
        
        # Получаем также донаты за предыдущий месяц для тренда
        prev_month = today.replace(day=1) - timedelta(days=1)
        prev_month_start = int(prev_month.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0).timestamp())
        prev_month_end = start_of_month - 1
        
        prev_month_donations = list(donations_collection.find({
            'timestamp': {'$gte': prev_month_start, '$lte': prev_month_end}
        }))
        
        # Группируем донаты за предыдущий месяц
        prev_user_donations = {}
        for donation in prev_month_donations:
            user_id = donation.get('user_id')
            amount = donation.get('amount', 0)
            
            if user_id not in prev_user_donations:
                prev_user_donations[user_id] = {'amount': 0}
            
            prev_user_donations[user_id]['amount'] += amount
        
        # Получаем информацию о пользователях
        top_users = []
        for user_id, stats in user_donations.items():
            try:
                user = users_collection.find_one({'_id': ObjectId(user_id)})
                if user:
                    # Рассчитываем тренд
                    prev_amount = prev_user_donations.get(user_id, {}).get('amount', 0)
                    trend = 0
                    if prev_amount > 0:
                        trend = int(((stats['amount'] - prev_amount) / prev_amount) * 100)
                    
                    top_users.append({
                        'id': str(user['_id']),
                        'name': user.get('nickname', 'Гость'),
                        'telegram': user.get('username', 'unknown'),
                        'avatar': user.get('avatar', '/default-cat-avatar.png'),
                        'isOnline': (datetime.now().timestamp() - user.get('lastInteractionTime', 0) / 1000) < 3600,
                        'amount': stats['amount'],
                        'count': stats['count'],
                        'trend': trend
                    })
            except Exception:
                continue
        
        # Сортируем по сумме донатов
        top_users.sort(key=lambda x: x['amount'], reverse=True)
        
        return jsonify(top_users)
    
    except Exception as e:
        return {'error': str(e)}, 500

@stats_bp.route('/shelters', methods=['GET'])
def get_shelters():
    """Получить список приютов"""
    try:
        shelters = list(shelters_collection.find())
        
        # Преобразуем ObjectId в строки для JSON-совместимости
        shelters_json = json.loads(json_util.dumps(shelters))
        
        # Добавляем статистику пожертвований
        for shelter in shelters_json:
            shelter_id = shelter.get('_id')
            
            # Общая сумма пожертвований
            shelter['total_donations'] = sum(
                donation.get('amount', 0) 
                for donation in donations_collection.find({'shelter_id': shelter_id})
            )
            
            # Пожертвования за текущий месяц
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_of_month = int(current_month.timestamp())
            
            shelter['month_donations'] = sum(
                donation.get('amount', 0) 
                for donation in donations_collection.find({
                    'shelter_id': shelter_id,
                    'timestamp': {'$gte': start_of_month}
                })
            )
        
        return jsonify(shelters_json)
    
    except Exception as e:
        return {'error': str(e)}, 500

@stats_bp.route('/init_data', methods=['POST'])
def init_data():
    """Инициализация данных в базе (для тестирования)"""
    try:
        # Создаем тестовый приют, если его еще нет
        if shelters_collection.count_documents({}) == 0:
            shelter = {
                'name': 'Котодом',
                'address': 'г. Москва, ул. Примерная, 123',
                'description': 'Приют для бездомных котиков',
                'website': 'https://kotodom.ru',
                'created_at': int(time.time())
            }
            shelters_collection.insert_one(shelter)
        
        # Добавляем тестовый донат, если нет донатов
        if donations_collection.count_documents({}) == 0:
            # Проверяем, есть ли хотя бы один пользователь
            user = users_collection.find_one()
            if user:
                donation = {
                    'user_id': str(user['_id']),
                    'amount': 1000,
                    'timestamp': int(time.time()),
                    'donation_type': 'shelter'
                }
                donations_collection.insert_one(donation)
        
        return {'status': 'success', 'message': 'Тестовые данные добавлены'}
    
    except Exception as e:
        return {'error': str(e)}, 500