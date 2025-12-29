#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from pymongo import MongoClient

def strip_html(html_text):
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_title_from_html(html_text):
    match = re.search(r'<h[12]>(.*?)</h[12]>', html_text)
    if match:
        return strip_html(match.group(1))
    
    text = strip_html(html_text)
    if len(text) > 100:
        return text[:97] + "..."
    return text if text else "Untitled"

def safe_text(text):
    return text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')

def export_for_indexer(output_file='indexer_input.tsv', limit=None):
    
    print("Подключение к MongoDB...")
    client = MongoClient('localhost', 27017)
    db = client['turkish_wiki_search']
    collection = db['documents']
    
    total = collection.count_documents({})
    print(f"Найдено документов: {total}")
    
    if limit:
        total = min(total, limit)
        print(f"Экспортируем первые {limit} документов")
    
    print(f"Экспорт в {output_file}...")
    
    exported = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        query = collection.find({}, {'url': 1, 'html_content': 1, '_id': 0})
        
        if limit:
            query = query.limit(limit)
        
        for doc_id, doc in enumerate(query, 1):
            url = doc.get('url', '')
            html_content = doc.get('html_content', '')
            
            title = extract_title_from_html(html_content)
            clean_text = strip_html(html_content)
            
            if not clean_text or len(clean_text) < 100:
                continue
            
            # TSV формат: doc_id \t url \t title \t content
            line = f"{doc_id}\t{safe_text(url)}\t{safe_text(title)}\t{safe_text(clean_text)}\n"
            f.write(line)
            
            exported += 1
            
            if exported % 100 == 0:
                print(f"  Экспортировано: {exported}/{total}")
    
    client.close()
    
    print(f"\nЭкспортировано {exported} документов")
    print(f"  Файл: {output_file}")
    
    return exported

if __name__ == '__main__':
    limit = None
    output_file = 'indexer_input.tsv'
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            output_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    export_for_indexer(output_file, limit)

