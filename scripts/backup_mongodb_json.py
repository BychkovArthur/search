#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
from pymongo import MongoClient
from datetime import datetime

def backup_mongodb(output_file='mongodb_backup.json'):
    print("=== Экспорт MongoDB базы данных ===")
    print()
    
    try:
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        db = client['turkish_wiki_search']
        collection = db['documents']
        
        count = collection.count_documents({})
        print(f"Найдено документов: {count}")
        print()
        
        print(f"Экспорт в {output_file}...")
        
        documents = []
        processed = 0
        
        for doc in collection.find():
            # Конвертируем ObjectId в строку
            doc['_id'] = str(doc['_id'])
            documents.append(doc)
            processed += 1
            
            if processed % 1000 == 0:
                print(f"  Обработано: {processed}/{count}")
        
        # Сохраняем в JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'database': 'turkish_wiki_search',
                'collection': 'documents',
                'export_date': datetime.now().isoformat(),
                'count': len(documents),
                'documents': documents
            }, f, ensure_ascii=False, indent=2)
        
        # Статистика
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        
        print()
        print("Экспорт завершен успешно!")
        print(f"  Документов: {len(documents)}")
        print(f"  Размер: {size_mb:.1f} MB")
        print(f"  Файл: {output_file}")
        print()
        print("Для сжатия:")
        print(f"  gzip {output_file}")
        print()
        print("Для восстановления:")
        print(f"  python3 scripts/restore_mongodb_json.py {output_file}")
        
        client.close()
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        sys.exit(1)

if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'mongodb_backup.json'
    backup_mongodb(output)

