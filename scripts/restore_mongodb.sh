#!/bin/bash

BACKUP_DIR="mongodb_backup"
DB_NAME="turkish_wiki_search"

echo "=== Восстановление MongoDB базы данных ==="
echo ""

if [ ! -d "$BACKUP_DIR/$DB_NAME" ]; then
    echo "ОШИБКА: Резервная копия не найдена"
    echo "Ожидается: $BACKUP_DIR/$DB_NAME/"
    echo ""
    echo "Если есть архив, распакуйте:"
    echo "  tar -xzf mongodb_backup.tar.gz"
    exit 1
fi

if ! command -v mongorestore &> /dev/null; then
    echo "ОШИБКА: mongorestore не найден"
    echo "Установите: sudo apt install mongodb-database-tools"
    exit 1
fi

if ! python3 -c "from pymongo import MongoClient; MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo "ОШИБКА: MongoDB недоступен"
    exit 1
fi

echo "Восстановление базы данных..."
mongorestore --db $DB_NAME $BACKUP_DIR/$DB_NAME/ --drop

if [ $? -eq 0 ]; then
    DOCS_COUNT=$(python3 -c "from pymongo import MongoClient; print(MongoClient('localhost', 27017)['$DB_NAME']['documents'].count_documents({}))")
    
    echo ""
    echo "Восстановление завершено!"
    echo "  Документов: $DOCS_COUNT"
else
    echo "ОШИБКА при восстановлении"
    exit 1
fi

