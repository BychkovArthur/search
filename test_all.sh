#!/bin/bash

echo "=== ПРОВЕРКА ПРОЕКТА ==="
echo ""

echo "1. Компиляция всех компонент..."
make clean > /dev/null 2>&1
if make all 2>&1 | grep -q "error"; then
    echo "   ОШИБКА компиляции"
    exit 1
else
    echo "   OK - все скомпилировано без ошибок"
fi

echo ""
echo "2. Проверка токенизатора..."
result=$(echo "istanbul ankara" | ./tokenize | head -2)
if [ -z "$result" ]; then
    echo "   ОШИБКА - токенизатор не работает"
    exit 1
else
    echo "   OK - токенизатор работает"
fi

echo ""
echo "3. Проверка стеммера..."
if ./test_stemmer > /dev/null 2>&1; then
    echo "   OK - стеммер работает"
else
    echo "   ОШИБКА - стеммер не работает"
    exit 1
fi

echo ""
echo "4. Проверка поисковика..."
if [ -f "index_stemmed.meta" ]; then
    result=$(echo "istanbul" | ./search index_stemmed 2>/dev/null | grep "Найдено:")
    if [ -z "$result" ]; then
        echo "   ОШИБКА - поисковик не работает"
        exit 1
    else
        echo "   OK - поисковик работает"
    fi
else
    echo "   ВНИМАНИЕ - индекс не найден (нужно построить)"
fi

echo ""
echo "5. Проверка утилит..."
if [ -f "dump_index" ] && [ -f "build_index" ]; then
    echo "   OK - все утилиты на месте"
else
    echo "   ОШИБКА - не хватает утилит"
    exit 1
fi

echo ""
echo "=== ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ==="
echo ""
echo "Структура проекта:"
echo "  src/       - исходники C++"
echo "  scripts/   - Python и shell скрипты"
echo "  tests/     - тестовые данные"
echo "  results/   - результаты анализа"
echo "  templates/ - HTML шаблоны"
echo ""
echo "Основные файлы:"
echo "  REPORT.md  - полный отчет по всем лабам"
echo "  README.md  - инструкции по использованию"
echo "  Makefile   - сборка проекта"
echo ""

