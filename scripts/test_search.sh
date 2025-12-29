#!/bin/bash

set -e

echo "=========================================="
echo "Тестирование поисковой системы (ЛР7)"
echo "=========================================="
echo

# Проверка наличия индекса
if [ ! -f "index.meta" ]; then
    echo "ОШИБКА: Индекс не найден. Сначала постройте индекс:"
    echo "  make build_index"
    echo "  ./build_index indexer_input.tsv index"
    exit 1
fi

if [ ! -f "search" ]; then
    echo "Компиляция поисковика..."
    make search
    echo
fi

echo "=== ТЕСТ 1: Простые запросы ==="
echo

echo "Запрос: buffalo"
./search index "buffalo" | grep "Найдено документов:"

echo "Запрос: the"
./search index "the" | grep "Найдено документов:"

echo "Запрос: istanbul"
./search index "istanbul" | grep "Найдено документов:"

echo

echo "=== ТЕСТ 2: Булевы операторы AND ==="
echo

echo "Запрос: istanbul && ankara"
./search index "istanbul && ankara" | grep "Найдено документов:"

echo "Запрос: the && istanbul"
./search index "the && istanbul" | grep "Найдено документов:"

echo

echo "=== ТЕСТ 3: Булевы операторы OR ==="
echo

echo "Запрос: istanbul || ankara"
./search index "istanbul || ankara" | grep "Найдено документов:"

echo "Запрос: buffalo || york"
./search index "buffalo || york" | grep "Найдено документов:"

echo

echo "=== ТЕСТ 4: Булевы операторы NOT ==="
echo

echo "Запрос: istanbul && !ankara"
./search index "istanbul && !ankara" | grep "Найдено документов:"

echo "Запрос: the && !buffalo"
./search index "the && !buffalo" | grep "Найдено документов:"

echo

echo "=== ТЕСТ 5: Сложные запросы со скобками ==="
echo

echo "Запрос: (istanbul || ankara) && turkey"
./search index "(istanbul || ankara) && turkey" | grep "Найдено документов:"

echo "Запрос: (the || a) && !wikipedia"
./search index "(the || a) && !wikipedia" | grep "Найдено документов:"

echo

echo "=== ТЕСТ 6: Несуществующие термы ==="
echo

echo "Запрос: xyznonexistent"
./search index "xyznonexistent" | grep "Найдено документов:"

echo "Запрос: buffalo && xyznonexistent"
./search index "buffalo && xyznonexistent" | grep "Найдено документов:"

echo

echo "=== ТЕСТ 7: Пакетная обработка запросов ==="
echo

if [ -f "tests/search_queries.txt" ]; then
    echo "Обработка запросов из файла..."
    total_queries=$(grep -v '^#' tests/search_queries.txt | grep -v '^$' | wc -l)
    echo "Всего запросов: $total_queries"
    
    time ./search index < tests/search_queries.txt > /tmp/search_results.txt 2>&1
    
    results_count=$(grep "Найдено документов:" /tmp/search_results.txt | wc -l)
    echo "Обработано запросов: $results_count"
fi

echo

echo "=== ТЕСТ 8: Измерение производительности ==="
echo

echo "Замер времени для 100 запросов 'the':"
time for i in {1..100}; do
    ./search index "the" > /dev/null 2>&1
done

echo

echo "=========================================="
echo "Все тесты выполнены успешно!"
echo "=========================================="

