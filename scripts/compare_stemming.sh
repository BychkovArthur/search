#!/bin/bash

echo "=========================================="
echo "Сравнение качества поиска"
echo "Индекс БЕЗ стемминга vs СО стеммингом"
echo "=========================================="
echo

queries=(
    "istanbul"
    "istanbulda"
    "istanbuldan"
    "osmanlı"
    "osmanlılar"
    "tarih"
    "tarihinde"
    "savaş"
    "savaşlar"
    "türkiye"
    "türkiyede"
)

echo "Запрос                   | Без стемминга | Со стеммингом | Разница"
echo "------------------------|---------------|---------------|----------"

for query in "${queries[@]}"; do
    result1=$(./search index_no_stem "$query" 2>&1 | grep "Найдено документов:" | awk '{print $3}')
    result2=$(./search index_stemmed "$query" 2>&1 | grep "Найдено документов:" | awk '{print $3}')
    
    if [ -n "$result1" ] && [ -n "$result2" ]; then
        diff=$((result2 - result1))
        printf "%-24s| %-13s | %-13s | %+d\n" "$query" "$result1" "$result2" "$diff"
    fi
done

echo
echo "=========================================="
echo "Анализ результатов:"
echo "=========================================="
echo
echo "Положительные изменения (больше результатов):"
echo "  - Разные формы слова находят одинаковые документы"
echo "  - Улучшается полнота (recall)"
echo
echo "Отрицательные изменения (меньше результатов):"
echo "  - Возможна чрезмерная агрессивность стемминга"
echo "  - Могут объединяться разные по смыслу слова"

