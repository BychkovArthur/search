#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мониторинг прогресса поискового робота
Показывает статистику из MongoDB в реальном времени
"""

import sys
import yaml
import time
from datetime import datetime
from pymongo import MongoClient

def format_timestamp(ts):
    """Форматирование Unix timestamp"""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def format_size(size_bytes):
    """Форматирование размера"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_stats(collection, config):
    """Получить статистику из MongoDB"""
    target = config['logic']['target_document_count']
    
    # Общее количество
    total = collection.count_documents({})
    
    # По источникам
    sources = {}
    for doc in collection.aggregate([
        {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
    ]):
        sources[doc['_id']] = doc['count']
    
    # Последние добавленные
    recent = list(collection.find().sort('create_date', -1).limit(5))
    
    # Недавно обновленные
    updated = list(collection.find(
        {'update_date': {'$exists': True}}
    ).sort('update_date', -1).limit(5))
    
    # Средний размер
    pipeline = [
        {'$project': {'size': {'$strLenCP': '$html_content'}}},
        {'$group': {'_id': None, 'avg': {'$avg': '$size'}, 'total': {'$sum': '$size'}}}
    ]
    size_stats = list(collection.aggregate(pipeline))
    avg_size = size_stats[0]['avg'] if size_stats else 0
    total_size = size_stats[0]['total'] if size_stats else 0
    
    return {
        'total': total,
        'target': target,
        'progress': (total / target * 100) if target > 0 else 0,
        'sources': sources,
        'recent': recent,
        'updated': updated,
        'avg_size': avg_size,
        'total_size': total_size
    }

def print_stats(stats, watch_mode=False):
    """Вывод статистики"""
    if watch_mode:
        print("\033[2J\033[H")  # Очистка экрана
    
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "ПРОГРЕСС СКАЧИВАНИЯ" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    total = stats['total']
    target = stats['target']
    progress = stats['progress']
    
    # Последние добавленные (вверху, можно листать)
    if stats['recent']:
        print("🆕 Последние добавленные:")
        for doc in stats['recent'][:3]:
            title = doc.get('url', '').split('/wiki/')[-1][:40]
            date = format_timestamp(doc.get('create_date', 0))
            print(f"   • {title}")
            print(f"     {date}")
        print()
    
    # По источникам (вверху, можно листать)
    print("📁 По источникам:")
    for source, count in sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True):
        source_short = source[:50] + "..." if len(source) > 50 else source
        print(f"   • {source_short}: {count:,}")
    print()
    
    # Размер данных
    print(f"💾 Размер данных: {format_size(stats['total_size'])}")
    print(f"   Средний размер документа: {format_size(stats['avg_size'])}")
    print()
    
    # Обновленные
    if stats['updated']:
        print(f"🔄 Обновлено документов: {len(stats['updated'])}")
        print()
    
    print("─" * 70)
    print()
    
    # ГЛАВНОЕ ВНИЗУ - ВСЕГДА ВИДНО БЕЗ ПРОКРУТКИ
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 23 + "ТЕКУЩИЙ СТАТУС" + " " * 31 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Основная статистика
    print(f"📊 ДОКУМЕНТОВ: {total:,} / {target:,} ({progress:.1f}%)")
    
    # Прогресс-бар
    bar_width = 50
    filled = int(bar_width * progress / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"   [{bar}] {progress:.1f}%")
    print()
    
    # Оценка времени
    if progress > 0 and progress < 100:
        remaining = target - total
        # Предполагаем ~45 док/мин из последних измерений
        est_minutes = remaining / 45
        est_hours = est_minutes / 60
        if est_hours > 1:
            print(f"⏱  Осталось примерно: {est_hours:.1f} часов (~{est_minutes:.0f} минут)")
        else:
            print(f"⏱  Осталось примерно: {est_minutes:.0f} минут")
        print()
    
    if watch_mode:
        print("🔄 Обновление каждые 5 секунд... (Ctrl+C для выхода)")
    else:
        print("💡 Используйте --watch для постоянного мониторинга")
    
    print("─" * 70)

def main():
    """Главная функция"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    watch_mode = '--watch' in sys.argv or '-w' in sys.argv
    
    # Загрузка конфига
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Ошибка: файл конфигурации не найден: {config_path}")
        sys.exit(1)
    
    # Подключение к MongoDB
    try:
        db_config = config['db']
        client = MongoClient(
            host=db_config['host'],
            port=db_config['port'],
            serverSelectionTimeoutMS=5000
        )
        client.server_info()  # Проверка подключения
        
        db = client[db_config['database']]
        collection = db[db_config['collection']]
    except Exception as e:
        print(f"Ошибка подключения к MongoDB: {e}")
        print("\nУбедитесь что MongoDB запущен:")
        print("  sudo systemctl start mongodb")
        print("  или: docker run -d -p 27017:27017 mongo")
        sys.exit(1)
    
    # Мониторинг
    try:
        if watch_mode:
            while True:
                stats = get_stats(collection, config)
                print_stats(stats, watch_mode=True)
                time.sleep(5)
        else:
            stats = get_stats(collection, config)
            print_stats(stats, watch_mode=False)
    except KeyboardInterrupt:
        print("\n\nМониторинг остановлен")
    finally:
        client.close()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Использование:")
        print("  python3 monitor_crawler.py [config.yaml] [--watch|-w]")
        print()
        print("Опции:")
        print("  --watch, -w    Постоянный мониторинг (обновление каждые 5 сек)")
        print()
        print("Примеры:")
        print("  python3 monitor_crawler.py                # Одноразовый вывод статистики")
        print("  python3 monitor_crawler.py --watch        # Постоянный мониторинг")
        print("  python3 monitor_crawler.py config.yaml -w # С указанием конфига")
        sys.exit(0)
    
    main()

