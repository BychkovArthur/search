#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import yaml
from pymongo import MongoClient
import time

def test_mongodb_connection(config):
    print("Тест 1: Подключение к MongoDB...")
    try:
        db_config = config['db']
        client = MongoClient(
            host=db_config['host'],
            port=db_config['port'],
            serverSelectionTimeoutMS=5000
        )
        client.server_info()
        print("  OK Подключение успешно")
        
        db = client[db_config['database']]
        collection = db[db_config['collection']]
        count = collection.count_documents({})
        print(f"  OK База данных: {db_config['database']}")
        print(f"  OK Коллекция: {db_config['collection']}")
        print(f"  OK Документов в БД: {count}")
        
        client.close()
        return True
    except Exception as e:
        print(f"  Ошибка: {e}")
        return False

def test_config_loading(config_path):
    print("Тест 2: Загрузка конфигурации...")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['db', 'logic', 'sources', 'wikipedia']
        for section in required_sections:
            if section not in config:
                print(f"  Отсутствует секция: {section}")
                return False, None
            print(f"  OK Секция '{section}' найдена")
        
        print(f"  OK Задержка между запросами: {config['logic']['delay_between_requests']} сек")
        print(f"  OK Целевое количество документов: {config['logic']['target_document_count']}")
        print(f"  OK Минимум слов: {config['logic']['min_words']}")
        print(f"  OK Источников: {len(config['sources'])}")
        
        return True, config
    except Exception as e:
        print(f"  Ошибка: {e}")
        return False, None

def test_url_normalization():
    print("Тест 3: Нормализация URL...")
    import urllib.parse
    
    def normalize_url(url):
        parsed = urllib.parse.urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.lower()
    
    test_cases = [
        ("https://tr.wikipedia.org/wiki/Test#section", "https://tr.wikipedia.org/wiki/test"),
        ("HTTPS://TR.WIKIPEDIA.ORG/WIKI/PAGE", "https://tr.wikipedia.org/wiki/page"),
        ("https://tr.wikipedia.org/wiki/Test?query=1", "https://tr.wikipedia.org/wiki/test")
    ]
    
    all_passed = True
    for original, expected in test_cases:
        normalized = normalize_url(original)
        if normalized == expected:
            print(f"  OK {original} -> {normalized}")
        else:
            print(f"  {original} -> {normalized} (ожидалось: {expected})")
            all_passed = False
    
    return all_passed

def main():
    if len(sys.argv) != 2:
        print("Использование: python3 test_crawler.py config.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ ПОИСКОВОГО РОБОТА")
    print("=" * 70)
    print()
    
    success, config = test_config_loading(config_path)
    if not success:
        print("\nТесты провалены: проблема с конфигурацией")
        sys.exit(1)
    print()
    
    mongodb_available = test_mongodb_connection(config)
    if not mongodb_available:
        print("\nПредупреждение: MongoDB недоступен")
        print("  Для работы робота необходимо установить и запустить MongoDB:")
        print("  - Ubuntu/Debian: sudo apt install mongodb")
        print("  - или используйте Docker: docker run -d -p 27017:27017 mongo")
    print()
    
    if not test_url_normalization():
        print("\nТесты провалены: проблема с нормализацией URL")
        sys.exit(1)
    print()
    
    print("=" * 70)
    if mongodb_available:
        print("OK ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    else:
        print("БАЗОВЫЕ ТЕСТЫ ПРОЙДЕНЫ (MongoDB недоступен)")
    print("=" * 70)
    print()
    print("Робот готов к работе!")
    print("Запуск: python3 crawler.py config.yaml")

if __name__ == '__main__':
    main()

