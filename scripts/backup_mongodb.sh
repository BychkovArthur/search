#!/bin/bash

BACKUP_DIR="mongodb_backup"
DB_NAME="turkish_wiki_search"

echo "=== Экспорт MongoDB базы данных ==="
echo ""

if ! command -v mongodump &> /dev/null; then
    echo "ОШИБКА: mongodump не найден"
    echo "Установите: sudo apt install mongodb-database-tools"
    exit 1
fi

if ! python3 -c "from pymongo import MongoClient; MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo "ОШИБКА: MongoDB недоступен"
    exit 1
fi

echo "Создание резервной копии..."
mongodump --db $DB_NAME --out $BACKUP_DIR

if [ $? -eq 0 ]; then
    DOCS_COUNT=$(python3 -c "from pymongo import MongoClient; print(MongoClient('localhost', 27017)['$DB_NAME']['documents'].count_documents({}))")
    SIZE=$(du -sh $BACKUP_DIR | cut -f1)
    
    echo ""
    echo "Экспорт завершен успешно!"
    echo "  Документов: $DOCS_COUNT"
    echo "  Размер: $SIZE"
    echo "  Путь: $BACKUP_DIR/$DB_NAME/"
    echo ""
    echo "Для восстановления:"
    echo "  mongorestore --db $DB_NAME $BACKUP_DIR/$DB_NAME/"
    echo ""
    echo "Для переноса:"
    echo "  tar -czf mongodb_backup.tar.gz $BACKUP_DIR"
else
    echo "ОШИБКА при экспорте"
    exit 1
fi

