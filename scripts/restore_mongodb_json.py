#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import gzip
from pymongo import MongoClient
from bson import ObjectId

def restore_mongodb(input_file):
    print("=== Восстановление MongoDB базы данных ===")
    print()
    
    try:
        # Проверка файла
        if input_file.endswith('.gz'):
            print(f"Распаковка {input_file}...")
            with gzip.open(input_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print(f"Чтение {input_file}...")
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        db = client[data['database']]
        collection = db[data['collection']]
        
        print(f"База данных: {data['database']}")
        print(f"Коллекция: {data['collection']}")
        print(f"Документов для импорта: {data['count']}")
        print()
        
        # Очистка существующих данных
        print("Очистка существующей коллекции...")
        collection.delete_many({})
        
        # Импорт
        print("Импорт документов...")
        documents = data['documents']
        
        # Конвертируем _id обратно в ObjectId
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = ObjectId(doc['_id'])
        
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            collection.insert_many(batch)
            print(f"  Импортировано: {min(i+batch_size, len(documents))}/{len(documents)}")
        
        final_count = collection.count_documents({})
        
        print()
        print("Восстановление завершено!")
        print(f"  Документов в БД: {final_count}")
        
        client.close()
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python3 restore_mongodb_json.py <backup_file.json>")
        print("  или: python3 restore_mongodb_json.py <backup_file.json.gz>")
        sys.exit(1)
    
    restore_mongodb(sys.argv[1])

