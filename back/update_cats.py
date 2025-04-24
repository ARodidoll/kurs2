from pymongo import MongoClient
import sys

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['catclap_db']
cats_collection = db['cats']

def update_cats_rarity():
    # Получаем всех котов
    all_cats = list(cats_collection.find({}))
    print(f"Найдено {len(all_cats)} котов без категорий")
    
    updated = 0
    
    # Устанавливаем rarity на основе цены или других параметров
    for cat in all_cats:
        rarity = None
        price = cat.get('price', 0)
        
        # Проверяем наличие поля rarity
        if 'rarity' not in cat:
            # Определяем категорию по цене или другим признакам
            if price > 400 or cat.get('likes', 0) > 80:
                rarity = 'legendary'
            elif price > 100 or cat.get('likes', 0) > 40:
                rarity = 'rare'
            else:
                rarity = 'common'
                
            # Если rarity не был установлен, устанавливаем его по умолчанию
            if not rarity:
                rarity = 'common'
                
            # Обновляем запись в базе данных
            result = cats_collection.update_one(
                {'_id': cat['_id']},
                {'$set': {'rarity': rarity}}
            )
            
            if result.modified_count:
                updated += 1
                print(f"Обновлен кот {cat['name']}: установлена категория {rarity}")
    
    print(f"Обновлено {updated} котов")

if __name__ == "__main__":
    update_cats_rarity()
    print("Обновление завершено")