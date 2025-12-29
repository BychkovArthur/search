#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import subprocess
import time
import os

app = Flask(__name__)

INDEX_PATH = "index_stemmed"
SEARCH_BIN = "./search"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 50
    
    if not query:
        return render_template('search.html', 
                             query='', 
                             results=[], 
                             total=0,
                             time=0,
                             page=1,
                             total_pages=0)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [SEARCH_BIN, INDEX_PATH, query],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        results = []
        total_found = 0
        
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if 'Найдено документов:' in line:
                parts = line.split()
                try:
                    total_found = int(parts[2])
                except:
                    pass
            elif line.strip() and i > 5:
                if line.strip().startswith(tuple('0123456789')):
                    title = line.split('.', 1)[1].strip() if '.' in line else line.strip()
                    if i + 1 < len(lines):
                        url = lines[i + 1].strip()
                        if url and not url.startswith(tuple('0123456789')):
                            results.append({
                                'title': title[:200],
                                'url': url
                            })
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = results[start_idx:end_idx]
        total_pages = (len(results) + per_page - 1) // per_page
        
        return render_template('search.html',
                             query=query,
                             results=page_results,
                             total=total_found,
                             time=elapsed,
                             page=page,
                             total_pages=total_pages,
                             start_idx=start_idx)
    
    except subprocess.TimeoutExpired:
        return render_template('search.html',
                             query=query,
                             results=[],
                             total=0,
                             time=5000,
                             page=1,
                             total_pages=0,
                             error="Запрос выполнялся слишком долго (таймаут)")
    except Exception as e:
        return render_template('search.html',
                             query=query,
                             results=[],
                             total=0,
                             time=0,
                             page=1,
                             total_pages=0,
                             error=f"Ошибка выполнения поиска: {str(e)}")

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [SEARCH_BIN, INDEX_PATH, query],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        results = []
        total_found = 0
        
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if 'Найдено документов:' in line:
                parts = line.split()
                try:
                    total_found = int(parts[2])
                except:
                    pass
            elif line.strip() and i > 5:
                if line.strip().startswith(tuple('0123456789')):
                    title = line.split('.', 1)[1].strip() if '.' in line else line.strip()
                    if i + 1 < len(lines):
                        url = lines[i + 1].strip()
                        if url and not url.startswith(tuple('0123456789')):
                            results.append({
                                'title': title[:200],
                                'url': url
                            })
        
        return jsonify({
            'query': query,
            'total': total_found,
            'time_ms': elapsed,
            'results': results[:50]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(f'{INDEX_PATH}.meta'):
        print("ОШИБКА: Индекс не найден!")
        print("Постройте индекс: ./build_index indexer_input.tsv index_stemmed --stemming")
        exit(1)
    
    if not os.path.exists(SEARCH_BIN):
        print("ОШИБКА: Поисковик не найден!")
        print("Скомпилируйте: make search")
        exit(1)
    
    print("Запуск веб-сервера на http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

