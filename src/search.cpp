#include "searcher.h"
#include <cstdio>
#include <cstring>
#include <sys/time.h>
#include <unistd.h>

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

class QueryEvaluator {
private:
    BooleanQueryParser* parser;
    IndexLoader* loader;
    QueryToken current_token;
    
    void advance() {
        current_token = parser->next_token();
    }
    
    DynamicArray<uint32_t> parse_expression() {
        DynamicArray<uint32_t> left = parse_term();
        
        while (current_token.type == TOKEN_OR) {
            advance();
            DynamicArray<uint32_t> right = parse_term();
            left = union_postings(left.data, left.size, right.data, right.size);
        }
        
        return left;
    }
    
    DynamicArray<uint32_t> parse_term() {
        DynamicArray<uint32_t> left = parse_factor();
        
        while (current_token.type == TOKEN_AND || current_token.type == TOKEN_WORD) {
            if (current_token.type == TOKEN_AND) {
                advance();
            }
            DynamicArray<uint32_t> right = parse_factor();
            left = intersect_postings(left.data, left.size, right.data, right.size);
        }
        
        return left;
    }
    
    DynamicArray<uint32_t> parse_factor() {
        if (current_token.type == TOKEN_NOT) {
            advance();
            DynamicArray<uint32_t> operand = parse_factor();
            return negate_postings(operand.data, operand.size, loader->get_total_documents());
        }
        
        if (current_token.type == TOKEN_LPAREN) {
            advance();
            DynamicArray<uint32_t> result = parse_expression();
            if (current_token.type == TOKEN_RPAREN) {
                advance();
            }
            return result;
        }
        
        if (current_token.type == TOKEN_WORD) {
            const Term* term = loader->find_term(current_token.word);
            advance();
            
            if (term) {
                DynamicArray<uint32_t> result;
                for (uint32_t i = 0; i < term->document_frequency; i++) {
                    result.push_back(term->doc_ids[i]);
                }
                return result;
            } else {
                DynamicArray<uint32_t> empty;
                return empty;
            }
        }
        
        DynamicArray<uint32_t> empty;
        return empty;
    }
    
public:
    QueryEvaluator(BooleanQueryParser* p, IndexLoader* l) : parser(p), loader(l) {}
    
    DynamicArray<uint32_t> evaluate() {
        parser->reset();
        advance();
        return parse_expression();
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Использование: %s <index_base> [query]\n", argv[0]);
        printf("\nПримеры:\n");
        printf("  %s index                     # Интерактивный режим\n", argv[0]);
        printf("  %s index < queries.txt       # Пакетная обработка\n", argv[0]);
        printf("  %s index \"osmanlı\"           # Один запрос\n", argv[0]);
        printf("\nСинтаксис запросов:\n");
        printf("  пробел или && - логическое И\n");
        printf("  || - логическое ИЛИ\n");
        printf("  ! - логическое НЕ\n");
        printf("  ( ) - группировка\n");
        printf("\nПримеры запросов:\n");
        printf("  osmanlı imparatorluğu\n");
        printf("  (istanbul || ankara) tarih\n");
        printf("  türkiye !savaş\n");
        return 1;
    }
    
    const char* index_path = argv[1];
    
    printf("Загрузка индекса: %s\n", index_path);
    double load_start = get_time();
    
    IndexLoader loader;
    if (!loader.load(index_path)) {
        fprintf(stderr, "Ошибка загрузки индекса!\n");
        return 1;
    }
    
    double load_time = get_time() - load_start;
    printf("Индекс загружен за %.3f сек\n", load_time);
    printf("Документов: %u, Термов: %u\n\n", 
           loader.get_total_documents(), loader.get_total_terms());
    
    if (argc >= 3) {
        const char* query = argv[2];
        
        printf("Запрос: %s\n", query);
        double start = get_time();
        
        BooleanQueryParser parser(query);
        QueryEvaluator evaluator(&parser, &loader);
        DynamicArray<uint32_t> results = evaluator.evaluate();
        
        double elapsed = get_time() - start;
        
        printf("Найдено документов: %zu (%.3f мс)\n\n", results.size, elapsed * 1000);
        
        for (size_t i = 0; i < results.size && i < 50; i++) {
            const Document* doc = loader.get_document(results[i]);
            if (doc) {
                printf("%3zu. %s\n", i+1, doc->title);
                printf("     %s\n\n", doc->url);
            }
        }
        
        if (results.size > 50) {
            printf("... и еще %zu документов\n", results.size - 50);
        }
        
        return 0;
    }
    
    char query[1024];
    
    if (isatty(fileno(stdin))) {
        printf("Интерактивный режим. Введите запрос (Ctrl+D для выхода):\n");
    }
    
    while (true) {
        if (isatty(fileno(stdin))) {
            printf("> ");
            fflush(stdout);
        }
        
        if (!fgets(query, sizeof(query), stdin)) {
            break;
        }
        
        // Удаление перевода строки
        size_t len = strlen(query);
        if (len > 0 && query[len-1] == '\n') {
            query[len-1] = '\0';
            len--;
        }
        
        if (len == 0) continue;
        
        double start = get_time();
        
        BooleanQueryParser parser(query);
        QueryEvaluator evaluator(&parser, &loader);
        DynamicArray<uint32_t> results = evaluator.evaluate();
        
        double elapsed = get_time() - start;
        
        printf("Запрос: %s\n", query);
        printf("Найдено: %zu документов (%.3f мс)\n", results.size, elapsed * 1000);
        
        for (size_t i = 0; i < results.size && i < 10; i++) {
            const Document* doc = loader.get_document(results[i]);
            if (doc) {
                printf("%3zu. %s\n", i+1, doc->title);
                printf("     %s\n", doc->url);
            }
        }
        
        if (results.size > 10) {
            printf("... и еще %zu документов\n", results.size - 10);
        }
        
        printf("\n");
    }
    
    return 0;
}

