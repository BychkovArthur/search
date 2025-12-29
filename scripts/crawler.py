#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import yaml
import time
import hashlib
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING
import logging
import os

class WikipediaCrawler:
    
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
        
        self.logger.info("Робот инициализирован")
    
    def _setup_logging(self):
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        os.makedirs('logs', exist_ok=True)
        
        self.logger = logging.getLogger('WikiCrawler')
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
                self.logger.warning(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        return None
    
    def get_category_members(self, category, limit=5000):
        base_url = self.config['wikipedia']['base_url']
        all_titles = []
        cmcontinue = None
        
        self.logger.info(f"Получение статей из категории: {category}")
        
        while len(all_titles) < limit:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'categorymembers',
                'cmtitle': category,
                'cmlimit': min(500, limit - len(all_titles)),
                'cmnamespace': 0
            }
            
            if cmcontinue:
                params['cmcontinue'] = cmcontinue
            
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            try:
                data_str = self.fetch_with_retry(url)
                data = json.loads(data_str)
                
                if 'query' in data and 'categorymembers' in data['query']:
                    titles = [item['title'] for item in data['query']['categorymembers']]
                    all_titles.extend(titles)
                
                if 'continue' in data and 'cmcontinue' in data['continue']:
                    cmcontinue = data['continue']['cmcontinue']
                else:
                    break
                
                time.sleep(self.config['logic']['delay_between_requests'])
            except Exception as e:
                self.logger.error(f"Ошибка получения категории {category}: {e}")
                break
        
        self.logger.info(f"Получено {len(all_titles)} статей из {category}")
        return all_titles
    
    def get_random_articles(self, count=100):
        base_url = self.config['wikipedia']['base_url']
        all_titles = []
        
        self.logger.info(f"Получение {count} случайных статей")
        
        while len(all_titles) < count:
            batch_size = min(10, count - len(all_titles))
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'random',
                'rnnamespace': 0,
                'rnlimit': batch_size
            }
            
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            try:
                data_str = self.fetch_with_retry(url)
                data = json.loads(data_str)
                
                if 'query' in data and 'random' in data['query']:
                    titles = [item['title'] for item in data['query']['random']]
                    all_titles.extend(titles)
                
                time.sleep(self.config['logic']['delay_between_requests'])
            except Exception as e:
                self.logger.error(f"Ошибка получения случайных статей: {e}")
                break
        
        self.logger.info(f"Получено {len(all_titles)} случайных статей")
        return all_titles
    
    def fetch_article(self, title):
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
            self.logger.error(f"Ошибка получения статьи {title}: {e}")
            return None
    
    def count_words(self, html_content):
        text = re.sub('<[^<]+?>', '', html_content)
        words = re.findall(r'\w+', text)
        return len(words)
    
    def calculate_hash(self, content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def should_reindex(self, doc):
        reindex_period = self.config['logic']['reindex_period_days']
        crawl_date = datetime.fromtimestamp(doc['crawl_date'])
        age_days = (datetime.now() - crawl_date).days
        
        return age_days >= reindex_period
    
    def save_document(self, url, html_content, source, force_update=False):
        normalized_url = self.normalize_url(url)
        content_hash = self.calculate_hash(html_content)
        current_timestamp = int(time.time())
        
        existing = self.collection.find_one({'url': normalized_url})
        
        if existing:
            if existing.get('content_hash') == content_hash and not force_update:
                self.logger.debug(f"Документ не изменился: {normalized_url}")
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
            self.logger.info(f"Обновлен: {normalized_url}")
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
            self.logger.info(f"Добавлен: {normalized_url}")
            self.stats['new'] += 1
            return 'new'
    
    def crawl_source(self, source_config):
        source_name = source_config['name']
        source_type = source_config.get('type', 'wikipedia_category')
        
        self.logger.info(f"Начало обкачки источника: {source_name}")
        
        if source_type == 'wikipedia_random':
            target_count = source_config.get('batch_size', 1000)
            self.logger.info(f"Целевое количество случайных статей: {target_count}")
            
            processed = 0
            while processed < target_count:
                total_docs = self.collection.count_documents({})
                target = self.config['logic']['target_document_count']
                
                if total_docs >= target:
                    self.logger.info(f"Достигнуто целевое количество документов: {target}")
                    return
                
                batch = min(100, target_count - processed)
                titles = self.get_random_articles(batch)
                
                for title in titles:
                    try:
                        total_docs = self.collection.count_documents({})
                        if total_docs >= target:
                            self.logger.info(f"Достигнуто целевое количество документов: {target}")
                            return
                        
                        article = self.fetch_article(title)
                        
                        if not article or 'html' not in article:
                            continue
                        
                        word_count = self.count_words(article['html'])
                        min_words = self.config['logic']['min_words']
                        
                        if word_count < min_words:
                            self.logger.debug(f"Пропущено (мало слов): {title} ({word_count} слов)")
                            continue
                        
                        url = f"https://tr.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                        self.save_document(url, article['html'], source_name)
                        
                        processed += 1
                        self.stats['processed'] += 1
                        
                        time.sleep(self.config['logic']['delay_between_requests'])
                        
                        if self.stats['processed'] % 10 == 0:
                            self.print_stats()
                        
                    except KeyboardInterrupt:
                        self.logger.info("Получен сигнал остановки")
                        raise
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки {title}: {e}")
                        self.stats['errors'] += 1
                        continue
                        
            return
            
        else:
            category = source_config['category']
            titles = self.get_category_members(category, limit=5000)
        
        processed = 0
        for title in titles:
            try:
                total_docs = self.collection.count_documents({})
                target = self.config['logic']['target_document_count']
                
                if total_docs >= target:
                    self.logger.info(f"Достигнуто целевое количество документов: {target}")
                    return
                
                article = self.fetch_article(title)
                
                if not article or 'html' not in article:
                    continue
                
                word_count = self.count_words(article['html'])
                min_words = self.config['logic']['min_words']
                
                if word_count < min_words:
                    self.logger.debug(f"Пропущено (мало слов): {title} ({word_count} слов)")
                    continue
                
                url = f"https://tr.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                self.save_document(url, article['html'], source_name)
                
                processed += 1
                self.stats['processed'] += 1
                
                time.sleep(self.config['logic']['delay_between_requests'])
                
                if processed % 10 == 0:
                    self.print_stats()
                
            except KeyboardInterrupt:
                self.logger.info("Получен сигнал остановки")
                raise
            except Exception as e:
                self.logger.error(f"Ошибка обработки {title}: {e}")
                self.stats['errors'] += 1
                continue
    
    def reindex_old_documents(self):
        self.logger.info("Проверка документов для переобкачки...")
        
        reindex_period = self.config['logic']['reindex_period_days']
        cutoff_timestamp = int(time.time()) - (reindex_period * 86400)
        
        old_docs = self.collection.find({
            'crawl_date': {'$lt': cutoff_timestamp}
        })
        
        count = 0
        for doc in old_docs:
            try:
                url = doc['url']
                title = url.split('/wiki/')[-1] if '/wiki/' in url else None
                
                if not title:
                    continue
                
                title = urllib.parse.unquote(title)
                
                article = self.fetch_article(title)
                
                if article and 'html' in article:
                    self.save_document(url, article['html'], doc['source'], force_update=True)
                    count += 1
                
                time.sleep(self.config['logic']['delay_between_requests'])
                
            except KeyboardInterrupt:
                self.logger.info("Получен сигнал остановки")
                raise
            except Exception as e:
                self.logger.error(f"Ошибка переобкачки {doc['url']}: {e}")
                continue
        
        self.logger.info(f"Переобкачано документов: {count}")
    
    def print_stats(self):
        total = self.collection.count_documents({})
        target = self.config['logic']['target_document_count']
        progress = (total / target * 100) if target > 0 else 0
        
        self.logger.info(
            f"Статистика: обработано={self.stats['processed']}, "
            f"новых={self.stats['new']}, обновлено={self.stats['updated']}, "
            f"пропущено={self.stats['skipped']}, ошибок={self.stats['errors']}, "
            f"всего в БД={total}/{target} ({progress:.1f}%)"
        )
    
    def run(self):
        self.logger.info("Запуск поискового робота")
        self.logger.info(f"Целевое количество документов: {self.config['logic']['target_document_count']}")
        
        try:
            for source in self.config['sources']:
                total_docs = self.collection.count_documents({})
                target = self.config['logic']['target_document_count']
                
                if total_docs >= target:
                    self.logger.info("Достигнуто целевое количество документов")
                    break
                
                self.crawl_source(source)
            
            self.reindex_old_documents()
            
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
        print("Использование: python3 crawler.py <путь к config.yaml>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"Ошибка: файл конфигурации не найден: {config_path}")
        sys.exit(1)
    
    crawler = WikipediaCrawler(config_path)
    crawler.run()

if __name__ == '__main__':
    main()

