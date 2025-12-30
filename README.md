# Поисковая система по турецкой Википедии

Учебный проект - система информационного поиска с булевым индексом и стеммингом для турецкого языка.

Json со всеми документами [тут](https://disk.yandex.ru/d/3nad64iIJ1OtVw)

## Быстрый старт

```bash
# 1. Компиляция
make all

# 2. Тест токенизатора
echo "istanbul ankara" | ./tokenize

# 3. Поиск (если индекс построен)
./search index_stemmed "istanbul"

# 4. Веб-интерфейс
python3 web_search.py
# Открыть http://localhost:5000

# 5. Проверка всех компонент
./test_all.sh
```

## Компиляция

```bash
make clean
make all
```

Будут созданы:
- `tokenize` - токенизатор
- `build_index` - построение индекса
- `search` - поисковая система
- `dump_index` - просмотр индекса
- `test_stemmer` - тесты стеммера

## Использование

### Токенизация (ЛР3)

```bash
# Из файла
./tokenize < tests/test_input.txt

# Из строки
echo "Osmanlı İmparatorluğu tarihi" | ./tokenize
```

### Построение индекса (ЛР6)

```bash
# Экспорт из MongoDB и построение индекса
python3 scripts/export_for_indexer_tsv.py
./build_index indexer_input.tsv index_no_stem

# Со стеммингом
./build_index indexer_input.tsv index_stemmed --stemming
```

### Поиск (ЛР7)

#### CLI поиск
```bash
# Простой запрос
./search index_stemmed "istanbul"

# Булевы операторы
./search index_stemmed "istanbul && ankara"
./search index_stemmed "istanbul || ankara"
./search index_stemmed "istanbul && !ankara"
./search index_stemmed "(istanbul || ankara) && turkey"

# Интерактивный режим
./search index_stemmed
```

#### Веб-интерфейс
```bash
python3 web_search.py
# Открыть http://localhost:5000
```

### Тестирование стеммера (ЛР5)

```bash
./test_stemmer
```

## Поисковый робот (ЛР2)

```bash
# Быстрый многопоточный робот (рекомендуется)
./start_fast_crawler.sh

# Базовый робот
python3 scripts/crawler.py config.yaml

# Мониторинг
python3 scripts/monitor_crawler.py config.yaml

# Остановка
./scripts/stop_crawler.sh
```

Настройки в `config.yaml`

### Экспорт/импорт БД

```bash
# Экспорт базы данных
./scripts/backup_mongodb.sh

# Создать архив для переноса
tar -czf mongodb_backup.tar.gz mongodb_backup/

# Восстановление
./scripts/restore_mongodb.sh
```

## Анализ корпуса

### Загрузка примеров (ЛР1)
```bash
python3 scripts/fetch_quality_articles.py
python3 scripts/analyze_corpus.py
```

### Закон Ципфа (ЛР4)
```bash
./scripts/tokenize_corpus.sh
python3 scripts/zipf_analysis.py results/corpus_tokens.txt
```

## Тестовые скрипты

```bash
./test_all.sh                    # Быстрая проверка всех компонент
./check_all_labs.sh              # Проверка всех лабораторных
./scripts/test_search.sh         # Тесты поиска
./scripts/compare_stemming.sh    # Сравнение стемминга
```

## Структура проекта

```
poisk/
├── src/                   # Исходники C++
│   ├── tokenizer.cpp      # Токенизатор
│   ├── indexer.cpp/h      # Индексатор
│   ├── search.cpp         # Поисковик
│   ├── turkish_stemmer.h  # Стеммер
│   └── ...
├── scripts/               # Python/shell скрипты
├── templates/             # HTML шаблоны
├── tests/                 # Тестовые данные
├── results/               # Результаты анализа
├── data/                  # Примеры документов
├── Makefile               # Сборка проекта
├── config.yaml            # Конфиг робота
├── requirements.txt       # Python зависимости
└── report_labs.tex        # Отчет (LaTeX)
```

## Требования

### Обязательные
- g++ с поддержкой C++11
- Python 3.6+

### Опциональные
- MongoDB (для робота)
- Python пакеты: `pip3 install -r requirements.txt`

## Формат индекса

Индекс состоит из 3 файлов:
- `*.meta` - метаданные (кол-во документов, термов)
- `*.forward` - прямой индекс (документы)
- `*.inverted` - обратный индекс (термы → документы)

## Полезные команды

```bash
./dump_index index_stemmed       # Просмотр индекса
python3 test_web_api.py          # API тест
make clean                       # Очистка
```

## Отчеты

- **LaTeX отчет**: `report_labs.tex` (компилировать с pdflatex)
- **PDF**: `report.pdf`
