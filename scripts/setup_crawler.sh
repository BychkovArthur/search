#!/bin/bash

set -e

echo "========================================"
echo "Поисковый робот - установка и запуск"
echo "========================================"
echo

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python 3 не найден"
    exit 1
fi
echo "Python 3: $(python3 --version)"

if ! command -v pip3 &> /dev/null; then
    echo "ОШИБКА: pip3 не найден"
    exit 1
fi
echo "pip3 найден"

if ! command -v mongod &> /dev/null; then
    echo "MongoDB не найден локально"
    echo "  Убедитесь, что MongoDB запущен или измените config.yaml"
else
    echo "MongoDB найден"
fi

echo
echo "Установка зависимостей..."
pip3 install -r requirements.txt --quiet

echo
echo "Зависимости установлены"
echo
echo "========================================"
echo "Для запуска робота используйте:"
echo "  python3 crawler.py config.yaml"
echo "========================================"

