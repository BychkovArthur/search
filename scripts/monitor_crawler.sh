#!/bin/bash

CONFIG=${1:-config.yaml}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Использование: ./monitor_crawler.sh [config.yaml]"
    echo
    echo "Показывает статус скачивания в реальном времени"
    echo "Обновление каждые 5 секунд, Ctrl+C для выхода"
    exit 0
fi

python3 monitor_crawler.py "$CONFIG" --watch

