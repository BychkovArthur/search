#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания качественных длинных статей из турецкой Википедии
Используем избранные и качественные статьи
"""

import json
import os
import time
import urllib.request
import urllib.parse
import re

def fetch_with_retry(url, max_retries=3):
    """Запрос с повторными попытками"""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'InfoSearchBot/1.0 (Educational Project)')
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"    Ошибка после {max_retries} попыток: {e}")
                return None
            time.sleep(1)
    return None

def fetch_category_members(category, limit=500, lang='tr'):
    """Получить все статьи из категории с пагинацией"""
    base_url = f'https://{lang}.wikipedia.org/w/api.php'
    all_titles = []
    cmcontinue = None
    
    while len(all_titles) < limit:
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': category,
            'cmlimit': 50,
            'cmnamespace': 0
        }
        
        if cmcontinue:
            params['cmcontinue'] = cmcontinue
        
        url = base_url + '?' + urllib.parse.urlencode(params)
        data = fetch_with_retry(url)
        
        if not data or 'query' not in data:
            break
        
        if 'categorymembers' in data['query']:
            titles = [item['title'] for item in data['query']['categorymembers']]
            all_titles.extend(titles)
        
        if 'continue' in data and 'cmcontinue' in data['continue']:
            cmcontinue = data['continue']['cmcontinue']
        else:
            break
        
        time.sleep(0.3)
    
    return all_titles[:limit]

def fetch_article_content(title, lang='tr'):
    """Получить содержимое статьи"""
    base_url = f'https://{lang}.wikipedia.org/w/api.php'
    
    params = {
        'action': 'query',
        'format': 'json',
        'titles': title,
        'prop': 'extracts|info',
        'exintro': False,
        'explaintext': False,
        'inprop': 'url'
    }
    
    url = base_url + '?' + urllib.parse.urlencode(params)
    data = fetch_with_retry(url)
    
    if data and 'query' in data and 'pages' in data['query']:
        pages = data['query']['pages']
        for page_id, page_data in pages.items():
            if page_id != '-1':
                return page_data
    return None

def count_words_in_html(html_content):
    """Подсчет слов в HTML"""
    text = re.sub('<[^<]+?>', '', html_content)
    words = re.findall(r'\w+', text)
    return len(words)

def save_article(article_data, source_dir, index):
    """Сохранить статью"""
    os.makedirs(source_dir, exist_ok=True)
    filename = os.path.join(source_dir, f'article_{index:04d}.json')
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    
    return filename

def main():
    print("=== Скачивание качественных статей из турецкой Википедии ===\n")
    
    # Очищаем старые данные
    os.system('rm -rf data/source1_regular data/source2_featured')
    
    # Источник 1: Избранные статьи (Seçkin maddeler)
    print("Источник 1: Избранные статьи (Seçkin maddeler)...")
    featured_titles = fetch_category_members('Kategori:Seçkin_maddeler', limit=100)
    print(f"  Получено {len(featured_titles)} заголовков")
    
    saved_s1 = 0
    for title in featured_titles:
        if saved_s1 >= 35:
            break
        
        article = fetch_article_content(title)
        if not article or 'extract' not in article:
            continue
        
        word_count = count_words_in_html(article['extract'])
        
        # Сохраняем статьи с более чем 200 слов
        if word_count >= 200:
            article_data = {
                'title': article.get('title', title),
                'url': article.get('fullurl', ''),
                'content': article['extract'],
                'source': 'Turkish Wikipedia - Featured Articles',
                'word_count': word_count
            }
            
            filename = save_article(article_data, 'data/source1_regular', saved_s1 + 1)
            print(f"  OK {saved_s1+1}. {title[:50]}... ({word_count} слов)")
            saved_s1 += 1
        
        time.sleep(0.5)
    
    print(f"\nOK Источник 1: Сохранено {saved_s1} статей\n")
    print("="*70 + "\n")
    
    # Источник 2: Пробуем разные категории качественных статей
    print("Источник 2: Длинные статьи из разных категорий...")
    
    # Пробуем несколько категорий
    categories_to_try = [
        'Kategori:Vikipedi_iyi_maddeleri',
        'Kategori:Vikipedi_seçkin_listeleri',
        'Kategori:Osmanlı_İmparatorluğu',
        'Kategori:Türkiye_tarihi',
        'Kategori:Tarih',
        'Kategori:Ülkeler',
        'Kategori:Şehirler',
        'Kategori:Bilim',
        'Kategori:Edebiyat',
        'Kategori:Fizik',
        'Kategori:Kimya',
        'Kategori:Biyoloji'
    ]
    
    good_titles = []
    for cat in categories_to_try:
        titles = fetch_category_members(cat, limit=150)
        good_titles.extend(titles)
        print(f"    {cat}: {len(titles)} статей")
        if len(good_titles) >= 500:
            break
    
    print(f"  Всего получено {len(good_titles)} заголовков")
    
    saved_s2 = 0
    for title in good_titles:
        if saved_s2 >= 35:
            break
        
        article = fetch_article_content(title)
        if not article or 'extract' not in article:
            continue
        
        word_count = count_words_in_html(article['extract'])
        
        if word_count >= 200:
            article_data = {
                'title': article.get('title', title),
                'url': article.get('fullurl', ''),
                'content': article['extract'],
                'source': 'Turkish Wikipedia - Good Articles',
                'word_count': word_count
            }
            
            filename = save_article(article_data, 'data/source2_featured', saved_s2 + 1)
            print(f"  OK {saved_s2+1}. {title[:50]}... ({word_count} слов)")
            saved_s2 += 1
        
        time.sleep(0.5)
    
    print(f"\nOK Источник 2: Сохранено {saved_s2} статей")
    print("\n" + "="*70)
    print(f"Всего сохранено: {saved_s1 + saved_s2} статей")
    print("="*70)

if __name__ == '__main__':
    main()

