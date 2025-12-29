# Makefile для поисковой системы

CXX = g++
CXXFLAGS = -std=c++11 -Wall -O2 -DUTF8 -Isrc
LDFLAGS = 
SRCDIR = src
SCRIPTSDIR = scripts

all: tokenize build_index search dump_index test_stemmer

tokenize: $(SRCDIR)/tokenizer.cpp
	$(CXX) $(CXXFLAGS) -o tokenize $(SRCDIR)/tokenizer.cpp $(LDFLAGS)

indexer.o: $(SRCDIR)/indexer.cpp $(SRCDIR)/indexer.h
	$(CXX) $(CXXFLAGS) -c $(SRCDIR)/indexer.cpp

build_index: $(SRCDIR)/build_index.cpp indexer.o
	$(CXX) $(CXXFLAGS) -o build_index $(SRCDIR)/build_index.cpp indexer.o $(LDFLAGS)

search: $(SRCDIR)/search.cpp $(SRCDIR)/searcher.h $(SRCDIR)/indexer.h
	$(CXX) $(CXXFLAGS) -o search $(SRCDIR)/search.cpp $(LDFLAGS)

dump_index: $(SRCDIR)/dump_index.cpp $(SRCDIR)/indexer.h
	$(CXX) $(CXXFLAGS) -o dump_index $(SRCDIR)/dump_index.cpp $(LDFLAGS)

test_stemmer: $(SRCDIR)/test_stemmer.cpp $(SRCDIR)/turkish_stemmer.h
	$(CXX) $(CXXFLAGS) -o test_stemmer $(SRCDIR)/test_stemmer.cpp $(LDFLAGS)

test: tokenize
	@echo "=== Запуск тестов токенизатора ==="
	./tokenize < tests/test_input.txt > tests/test_output.txt
	@echo "Тесты завершены"

index: build_index
	@echo "=== Экспорт документов из MongoDB ==="
	python3 $(SCRIPTSDIR)/export_for_indexer_tsv.py
	@echo ""
	@echo "=== Построение индекса ==="
	./build_index indexer_input.tsv index
	@echo ""
	@echo "Индекс построен"

clean:
	rm -f tokenize build_index search dump_index test_stemmer *.o indexer_input.tsv
	rm -f index.meta index.forward index.inverted

.PHONY: all test clean index

