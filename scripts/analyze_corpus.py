#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'head'}
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
    
    def handle_endtag(self, tag):
        self.current_tag = None
    
    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.text_parts.append(text)
    
    def get_text(self):
        return ' '.join(self.text_parts)

def extract_text_from_html(html_content):
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()

def count_words(text):
    words = re.findall(r'\w+', text)
    return len(words)

def analyze_directory(directory):
    stats = {
        'count': 0,
        'total_size_raw': 0,
        'total_size_text': 0,
        'total_words': 0,
        'articles': []
    }
    
    if not os.path.exists(directory):
        return stats
    
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(directory, filename)
        file_size = os.path.getsize(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        content = data.get('content', '')
        text = extract_text_from_html(content)
        
        text_size = len(text.encode('utf-8'))
        word_count = count_words(text)
        
        stats['count'] += 1
        stats['total_size_raw'] += file_size
        stats['total_size_text'] += text_size
        stats['total_words'] += word_count
        
        stats['articles'].append({
            'title': data.get('title', 'Unknown'),
            'url': data.get('url', ''),
            'raw_size': file_size,
            'text_size': text_size,
            'word_count': word_count,
            'text_preview': text[:200] + '...' if len(text) > 200 else text
        })
    
    return stats

def print_stats(stats, source_name):
    print(f"\n{'='*70}")
    print(f"Статистика для: {source_name}")
    print(f"{'='*70}")
    print(f"Количество документов: {stats['count']}")
    print(f"Общий размер сырых данных: {stats['total_size_raw']:,} байт ({stats['total_size_raw']/1024:.2f} КБ)")
    print(f"Общий размер текста: {stats['total_size_text']:,} байт ({stats['total_size_text']/1024:.2f} КБ)")
    print(f"Всего слов: {stats['total_words']:,}")
    
    if stats['count'] > 0:
        print(f"\nСредний размер документа (сырой): {stats['total_size_raw']/stats['count']:.2f} байт")
        print(f"Средний размер текста: {stats['total_size_text']/stats['count']:.2f} байт")
        print(f"Среднее количество слов: {stats['total_words']/stats['count']:.2f}")
    
    print(f"\n{'Примеры статей:':-^70}")
    for i, article in enumerate(stats['articles'][:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Слов: {article['word_count']}")
        print(f"   Размер текста: {article['text_size']} байт")
        print(f"   Превью: {article['text_preview'][:150]}...")

def main():
    print("=== Анализ корпуса документов ===")
    
    stats1 = analyze_directory('data/source1_regular')
    print_stats(stats1, "Источник 1: Турецкая Википедия - обычные статьи")
    
    stats2 = analyze_directory('data/source2_featured')
    print_stats(stats2, "Источник 2: Турецкая Википедия - избранные статьи")
    
    total_count = stats1['count'] + stats2['count']
    total_raw = stats1['total_size_raw'] + stats2['total_size_raw']
    total_text = stats1['total_size_text'] + stats2['total_size_text']
    total_words = stats1['total_words'] + stats2['total_words']
    
    print(f"\n{'='*70}")
    print(f"ОБЩАЯ СТАТИСТИКА")
    print(f"{'='*70}")
    print(f"Всего документов: {total_count}")
    print(f"Общий размер сырых данных: {total_raw:,} байт ({total_raw/1024:.2f} КБ)")
    print(f"Общий размер текста: {total_text:,} байт ({total_text/1024:.2f} КБ)")
    print(f"Всего слов: {total_words:,}")
    
    if total_count > 0:
        print(f"\nСредний размер документа: {total_raw/total_count:.2f} байт")
        print(f"Средний объем текста: {total_text/total_count:.2f} байт")
        print(f"Среднее количество слов на документ: {total_words/total_count:.2f}")
    
    summary = {
        'source1': {
            'name': 'Turkish Wikipedia - Regular Articles',
            'url': 'https://tr.wikipedia.org',
            'count': stats1['count'],
            'total_raw_size': stats1['total_size_raw'],
            'total_text_size': stats1['total_size_text'],
            'total_words': stats1['total_words']
        },
        'source2': {
            'name': 'Turkish Wikipedia - Featured Articles',
            'url': 'https://tr.wikipedia.org/wiki/Kategori:Seçkin_maddeler',
            'count': stats2['count'],
            'total_raw_size': stats2['total_size_raw'],
            'total_text_size': stats2['total_size_text'],
            'total_words': stats2['total_words']
        },
        'total': {
            'count': total_count,
            'total_raw_size': total_raw,
            'total_text_size': total_text,
            'total_words': total_words,
            'avg_doc_size': total_raw/total_count if total_count > 0 else 0,
            'avg_text_size': total_text/total_count if total_count > 0 else 0,
            'avg_words': total_words/total_count if total_count > 0 else 0
        }
    }
    
    with open('data/corpus_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\nСтатистика сохранена в data/corpus_statistics.json")

if __name__ == '__main__':
    main()

