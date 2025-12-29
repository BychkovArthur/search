#!/bin/bash

echo "=== Токенизация корпуса ===" >&2
echo >&2

if ! python3 -c "from pymongo import MongoClient; MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo "MongoDB недоступен" >&2
    exit 1
fi

echo "MongoDB доступен" >&2

if [ ! -f "tokenize" ]; then
    echo "Компиляция токенизатора..." >&2
    make tokenize
fi

echo "Токенизатор готов" >&2
echo >&2

echo "Экспорт и токенизация..." >&2
python3 export_from_mongodb.py | ./tokenize > corpus_tokens.txt 2> tokenize_stats.txt

echo >&2
echo "Завершено" >&2
echo "  Токены: corpus_tokens.txt" >&2
echo "  Статистика: tokenize_stats.txt" >&2
echo >&2

cat tokenize_stats.txt >&2

