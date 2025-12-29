#!/bin/bash

CONFIG=${1:-config.yaml}

echo "========================================="
echo "Запуск поискового робота в фоне"
echo "========================================="
echo

# Проверка наличия конфига
if [ ! -f "$CONFIG" ]; then
    echo "Ошибка: файл конфигурации не найден: $CONFIG"
    echo "Использование: ./start_crawler.sh [config.yaml]"
    exit 1
fi

mkdir -p logs

echo "Проверка MongoDB..."
if ! python3 -c "from pymongo import MongoClient; MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo "ВНИМАНИЕ: MongoDB недоступен!"
    echo "Робот не сможет работать без MongoDB."
    echo
    echo "Запустите MongoDB:"
    echo "  sudo systemctl start mongodb"
    echo "  или: docker run -d -p 27017:27017 --name mongo mongo"
    echo
    read -p "Продолжить запуск? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Запуск робота..."
nohup python3 crawler.py "$CONFIG" > logs/crawler_stdout.log 2>&1 &
PID=$!

echo $PID > logs/crawler.pid

echo
echo "Робот запущен в фоне"
echo "  PID: $PID"
echo "  Логи: logs/crawler.log"
echo "  Stdout: logs/crawler_stdout.log"
echo
echo "Мониторинг:"
echo "  ./monitor_crawler.sh     - статус и прогресс"
echo "  tail -f logs/crawler.log - логи в реальном времени"
echo
echo "Остановка:"
echo "  ./stop_crawler.sh        - безопасная остановка"
echo "  kill $PID                - или вручную"
echo

