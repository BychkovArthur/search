#!/bin/bash

PID_FILE="logs/crawler.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Робот не запущен (PID файл не найден)"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "Робот не запущен (процесс $PID не существует)"
    rm "$PID_FILE"
    exit 1
fi

echo "Остановка робота (PID: $PID)..."
kill -TERM $PID

for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "Робот остановлен"
        rm "$PID_FILE"
        exit 0
    fi
    sleep 1
done

echo "Робот не ответил на SIGTERM, принудительная остановка..."
kill -KILL $PID
rm "$PID_FILE"
echo "Робот принудительно остановлен"

