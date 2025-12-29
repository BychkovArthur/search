#!/bin/bash

echo "=== БЫСТРЫЙ КРАУЛЕР ТУРЕЦКОЙ ВИКИПЕДИИ ==="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python3 не установлен"
    exit 1
fi

if ! python3 -c "import pymongo, yaml" 2>/dev/null; then
    echo "Установка зависимостей..."
    pip3 install pymongo pyyaml
fi

CONFIG="config.yaml"

if [ ! -f "$CONFIG" ]; then
    echo "ОШИБКА: Файл конфигурации не найден: $CONFIG"
    exit 1
fi

echo "Проверка MongoDB..."
if ! python3 -c "from pymongo import MongoClient; MongoClient(serverSelectionTimeoutMS=2000).admin.command('ping')" 2>/dev/null; then
    echo "ПРЕДУПРЕЖДЕНИЕ: MongoDB не доступен на localhost:27017"
    echo "Запустите MongoDB перед использованием краулера"
    echo ""
    echo "Варианты запуска MongoDB:"
    echo "  1. Системный: sudo systemctl start mongodb"
    echo "  2. Docker: docker run -d -p 27017:27017 --name mongo mongo:latest"
    exit 1
fi

echo "MongoDB доступен"
echo ""
echo "Запуск быстрого краулера..."
echo "  - Многопоточная загрузка (5 потоков по умолчанию)"
echo "  - Батчи по 1000 статей"
echo "  - Остановка: Ctrl+C"
echo ""

python3 scripts/fast_crawler.py "$CONFIG"

