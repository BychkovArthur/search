#!/bin/bash

set -e

echo "========================================"
echo "Тестирование Лабораторной работы 1"
echo "Добыча корпуса документов"
echo "========================================"
echo

echo "[1/3] Проверка окружения..."
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python 3 не найден"
    exit 1
fi
echo "Python 3 найден: $(python3 --version)"
echo

if [ ! -d "data/source1_regular" ] || [ ! -d "data/source2_featured" ]; then
    echo "[2/3] Загрузка примеров статей..."
    python3 fetch_quality_articles.py
    echo
else
    echo "[2/3] Данные уже загружены, пропускаем..."
    echo
fi

echo "[3/3] Анализ корпуса документов..."
python3 analyze_corpus.py
echo

echo "========================================"
echo "Тестирование завершено успешно!"
echo "========================================"
echo
echo "Результаты:"
echo "- Примеры статей: data/source1_regular/, data/source2_featured/"
echo "- Статистика: data/corpus_statistics.json"
echo "- Отчет: REPORT.md"
echo "- Анализ поисковиков: existing_search_analysis.md"
echo

# Вывод краткой статистики
if [ -f "data/corpus_statistics.json" ]; then
    echo "Краткая статистика корпуса:"
    python3 -c "
import json
with open('data/corpus_statistics.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f\"  Источник 1: {data['source1']['count']} документов, {data['source1']['total_words']} слов\")
    print(f\"  Источник 2: {data['source2']['count']} документов, {data['source2']['total_words']} слов\")
    print(f\"  Итого: {data['total']['count']} документов, {data['total']['total_words']} слов\")
    print(f\"  Средний размер документа: {data['total']['avg_words']:.2f} слов\")
"
fi

