#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый многопоточный поисковый робот для турецкой Википедии
Оптимизированная версия с параллельной загрузкой
"""

import sys
import yaml
import time
import hashlib
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime
from pymongo import MongoClient, ASCENDING
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

class FastWikipediaCrawler:
    """Быстрый многопоточный поисковый робот"""
    
    def __init__(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self._setup_logging()
        self._connect_db()
        
        self.stats = {
            'processed': 0,
            'new': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        self.stats_lock = threading.Lock()
        
        self.num_workers = self.config['logic'].get('num_workers', 5)
        self.logger.info(f"Робот инициализирован с {self.num_workers} потоками")
    
    def _setup_logging(self):
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        os.makedirs('logs', exist_ok=True)
        
        self.logger = logging.getLogger('FastWikiCrawler')
        self.logger.setLevel(log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if log_config.get('file'):
            fh = logging.FileHandler(log_config['file'], encoding='utf-8')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        
        if log_config.get('console', True):
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
    
    def _connect_db(self):
        db_config = self.config['db']
        
        try:
            self.client = MongoClient(
                host=db_config['host'],
                port=db_config['port']
            )
            self.db = self.client[db_config['database']]
            self.collection = self.db[db_config['collection']]
            
            self.collection.create_index([('url', ASCENDING)], unique=True)
            self.collection.create_index([('source', ASCENDING)])
            self.collection.create_index([('crawl_date', ASCENDING)])
            
            self.logger.info(f"Подключено к MongoDB: {db_config['database']}.{db_config['collection']}")
        except Exception as e:
            self.logger.error(f"Ошибка подключения к MongoDB: {e}")
            raise
    
    def normalize_url(self, url):
        parsed = urllib.parse.urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.lower()
    
    def fetch_with_retry(self, url, max_retries=None):
        if max_retries is None:
            max_retries = self.config['logic']['max_retries']
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', self.config['wikipedia']['user_agent'])
                
                timeout = self.config['logic']['request_timeout']
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    raise
        return None
    
    def get_random_articles_batch(self, count=500):
        """Получить большой батч случайных статей за один раз"""
        base_url = self.config['wikipedia']['base_url']
        all_titles = []
        
        while len(all_titles) < count:
            batch_size = min(500, count - len(all_titles))
            params = {
                'action': 'query',
                'format': 'json',
                'generator': 'random',
                'grnnamespace': 0,
                'grnlimit': batch_size,
                'prop': 'info'
            }
            
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            try:
                data_str = self.fetch_with_retry(url)
                data = json.loads(data_str)
                
                if 'query' in data and 'pages' in data['query']:
                    titles = [page['title'] for page in data['query']['pages'].values()]
                    all_titles.extend(titles)
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Ошибка получения случайных статей: {e}")
                break
        
        return all_titles
    
    def fetch_article(self, title):
        """Получить содержимое статьи"""
        base_url = self.config['wikipedia']['base_url']
        
        params = {
            'action': 'parse',
            'format': 'json',
            'page': title,
            'prop': 'text|displaytitle',
            'disabletoc': 1
        }
        
        url = base_url + '?' + urllib.parse.urlencode(params)
        
        try:
            data_str = self.fetch_with_retry(url)
            data = json.loads(data_str)
            
            if 'parse' in data and 'text' in data['parse']:
                return {
                    'html': data['parse']['text']['*'],
                    'title': data['parse']['displaytitle'],
                    'pageid': data['parse']['pageid']
                }
            return None
        except Exception as e:
            self.logger.debug(f"Ошибка получения статьи {title}: {e}")
            return None
    
    def count_words(self, html_content):
        text = re.sub('<[^<]+?>', '', html_content)
        words = re.findall(r'\w+', text)
        return len(words)
    
    def calculate_hash(self, content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def save_document(self, url, html_content, source):
        """Сохранение документа в MongoDB"""
        normalized_url = self.normalize_url(url)
        content_hash = self.calculate_hash(html_content)
        current_timestamp = int(time.time())
        
        try:
            existing = self.collection.find_one({'url': normalized_url})
            
            if existing:
                if existing.get('content_hash') == content_hash:
                    with self.stats_lock:
                        self.stats['skipped'] += 1
                    return 'skipped'
                
                self.collection.update_one(
                    {'url': normalized_url},
                    {
                        '$set': {
                            'html_content': html_content,
                            'content_hash': content_hash,
                            'crawl_date': current_timestamp,
                            'update_date': current_timestamp
                        }
                    }
                )
                with self.stats_lock:
                    self.stats['updated'] += 1
                return 'updated'
            else:
                document = {
                    'url': normalized_url,
                    'html_content': html_content,
                    'source': source,
                    'content_hash': content_hash,
                    'crawl_date': current_timestamp,
                    'create_date': current_timestamp
                }
                
                self.collection.insert_one(document)
                with self.stats_lock:
                    self.stats['new'] += 1
                return 'new'
        except Exception as e:
            self.logger.error(f"Ошибка сохранения {normalized_url}: {e}")
            return 'error'
    
    def process_article(self, title, source_name):
        """Обработка одной статьи (выполняется в потоке)"""
        try:
            article = self.fetch_article(title)
            
            if not article or 'html' not in article:
                return None
            
            word_count = self.count_words(article['html'])
            min_words = self.config['logic']['min_words']
            
            if word_count < min_words:
                return None
            
            url = f"https://tr.wikipedia.org/wiki/{urllib.parse.quote(title)}"
            result = self.save_document(url, article['html'], source_name)
            
            with self.stats_lock:
                self.stats['processed'] += 1
            
            return result
            
        except Exception as e:
            with self.stats_lock:
                self.stats['errors'] += 1
            self.logger.debug(f"Ошибка обработки {title}: {e}")
            return None
    
    def crawl_parallel(self, titles, source_name):
        """Параллельная обкачка списка статей"""
        total = len(titles)
        self.logger.info(f"Начало параллельной обкачки {total} статей с {self.num_workers} потоками")
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {
                executor.submit(self.process_article, title, source_name): title 
                for title in titles
            }
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                
                if completed % 50 == 0:
                    self.print_stats()
                
                target = self.config['logic']['target_document_count']
                total_docs = self.collection.count_documents({})
                if total_docs >= target:
                    self.logger.info("Достигнуто целевое количество документов")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
    
    def print_stats(self):
        """Вывод статистики"""
        total = self.collection.count_documents({})
        target = self.config['logic']['target_document_count']
        progress = (total / target * 100) if target > 0 else 0
        
        with self.stats_lock:
            self.logger.info(
                f"Статистика: обработано={self.stats['processed']}, "
                f"новых={self.stats['new']}, обновлено={self.stats['updated']}, "
                f"пропущено={self.stats['skipped']}, ошибок={self.stats['errors']}, "
                f"всего в БД={total}/{target} ({progress:.1f}%)"
            )
    
    def run(self):
        """Запуск робота"""
        self.logger.info("Запуск быстрого поискового робота")
        self.logger.info(f"Целевое количество документов: {self.config['logic']['target_document_count']}")
        
        try:
            target = self.config['logic']['target_document_count']
            total_docs = self.collection.count_documents({})
            
            if total_docs >= target:
                self.logger.info("Целевое количество уже достигнуто")
                return
            
            remaining = target - total_docs
            self.logger.info(f"Осталось загрузить: {remaining} документов")
            
            batch_size = 1000
            while total_docs < target:
                self.logger.info(f"Получение батча из {batch_size} случайных статей...")
                titles = self.get_random_articles_batch(batch_size)
                
                if not titles:
                    self.logger.warning("Не удалось получить статьи")
                    break
                
                self.logger.info(f"Получено {len(titles)} статей для обработки")
                self.crawl_parallel(titles, "Turkish Wikipedia - Random (Fast)")
                
                total_docs = self.collection.count_documents({})
                if total_docs >= target:
                    break
            
            self.logger.info("=" * 70)
            self.logger.info("Обкачка завершена")
            self.print_stats()
            
        except KeyboardInterrupt:
            self.logger.info("\nРобот остановлен пользователем")
            self.print_stats()
        except Exception as e:
            self.logger.error(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            self.client.close()
            self.logger.info("Соединение с БД закрыто")

def main():
    if len(sys.argv) != 2:
        print("Использование: python3 fast_crawler.py <путь к config.yaml>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"Ошибка: файл конфигурации не найден: {config_path}")
        sys.exit(1)
    
    crawler = FastWikipediaCrawler(config_path)
    crawler.run()

if __name__ == '__main__':
    main()

