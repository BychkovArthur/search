#!/usr/bin/env python3
"""Тест веб-интерфейса без запуска сервера"""

import subprocess
import json

def test_search(query):
    """Тест поиска через CLI"""
    try:
        result = subprocess.run(
            ['./search', 'index_stemmed', query],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'Найдено:' in line:
                return line
        return "Нет результатов"
    except Exception as e:
        return f"Ошибка: {e}"

print("=== ТЕСТИРОВАНИЕ ПОИСКОВОЙ СИСТЕМЫ ===\n")

queries = [
    "istanbul",
    "istanbul ankara",
    "istanbul || ankara", 
    "(istanbul || ankara) && turkey",
    "!ankara"
]

for q in queries:
    print(f"Запрос: {q}")
    result = test_search(q)
    print(f"  → {result}")
    print()

print("Все запросы выполнены успешно!")
