#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pymongo import MongoClient
import re

def extract_text_from_html(html):
    # Удаление тегов
    text = re.sub(r'<[^>]+>', ' ', html)
    # Удаление множественных пробелов
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def main():
    try:
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        db = client['turkish_wiki_search']
        collection = db['documents']
        
        count = collection.count_documents({})
        print(f"# Найдено документов: {count}", file=sys.stderr)
        
        for doc in collection.find():
            html = doc.get('html_content', '')
            text = extract_text_from_html(html)
            
            print(text)
            
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()

if __name__ == '__main__':
    main()

