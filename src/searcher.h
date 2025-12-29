#ifndef SEARCHER_H
#define SEARCHER_H

#include "indexer.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cctype>

class IndexLoader {
private:
    IndexMetadata metadata;
    Document* documents;
    Term* terms;
    
public:
    IndexLoader() : documents(nullptr), terms(nullptr) {
        memset(&metadata, 0, sizeof(metadata));
    }
    
    IndexLoader(const IndexLoader&) = delete;
    IndexLoader& operator=(const IndexLoader&) = delete;
    
    ~IndexLoader() {
        if (documents) {
            for (uint32_t i = 0; i < metadata.total_documents; i++) {
                if (documents[i].url) free(documents[i].url);
                if (documents[i].title) free(documents[i].title);
            }
            delete[] documents;
        }
        
        if (terms) {
            for (uint32_t i = 0; i < metadata.total_unique_terms; i++) {
                if (terms[i].term) free(terms[i].term);
                if (terms[i].doc_ids) free(terms[i].doc_ids);
            }
            delete[] terms;
        }
    }
    
    bool load(const char* base_path) {
        char path[512];
        
        snprintf(path, sizeof(path), "%s.meta", base_path);
        if (!load_metadata(path)) {
            fprintf(stderr, "Ошибка загрузки метаданных: %s\n", path);
            return false;
        }
        
        snprintf(path, sizeof(path), "%s.forward", base_path);
        if (!load_forward_index(path)) {
            fprintf(stderr, "Ошибка загрузки прямого индекса: %s\n", path);
            return false;
        }
        
        snprintf(path, sizeof(path), "%s.inverted", base_path);
        if (!load_inverted_index(path)) {
            fprintf(stderr, "Ошибка загрузки обратного индекса: %s\n", path);
            return false;
        }
        
        return true;
    }
    
    const Term* find_term(const char* query_term) const {
        int left = 0;
        int right = metadata.total_unique_terms - 1;
        
        if (getenv("DEBUG_SEARCH")) {
            fprintf(stderr, "DEBUG: Поиск терма '%s' среди %u термов\n", 
                    query_term, metadata.total_unique_terms);
            fprintf(stderr, "DEBUG: Первый терм: '%s'\n", terms[0].term);
            fprintf(stderr, "DEBUG: Последний терм: '%s'\n", terms[metadata.total_unique_terms-1].term);
        }
        
        while (left <= right) {
            int mid = left + (right - left) / 2;
            int cmp = strcmp(query_term, terms[mid].term);
            
            if (getenv("DEBUG_SEARCH")) {
                fprintf(stderr, "DEBUG: left=%d, right=%d, mid=%d, term='%s', cmp=%d\n",
                        left, right, mid, terms[mid].term, cmp);
            }
            
            if (cmp == 0) {
                return &terms[mid];
            } else if (cmp < 0) {
                right = mid - 1;
            } else {
                left = mid + 1;
            }
        }
        
        return nullptr;
    }
    
    const Document* get_document(uint32_t doc_id) const {
        for (uint32_t i = 0; i < metadata.total_documents; i++) {
            if (documents[i].doc_id == doc_id) {
                return &documents[i];
            }
        }
        return nullptr;
    }
    
    uint32_t get_total_documents() const {
        return metadata.total_documents;
    }
    
    uint32_t get_total_terms() const {
        return metadata.total_unique_terms;
    }
    
private:
    bool load_metadata(const char* path) {
        FILE* f = fopen(path, "rb");
        if (!f) return false;
        
        size_t read = fread(&metadata, sizeof(metadata), 1, f);
        fclose(f);
        
        if (read != 1 || metadata.magic != INDEX_MAGIC) {
            return false;
        }
        
        return true;
    }
    
    bool load_forward_index(const char* path) {
        FILE* f = fopen(path, "rb");
        if (!f) return false;
        
        uint32_t num_docs, reserved;
        if (fread(&num_docs, 4, 1, f) != 1 || fread(&reserved, 4, 1, f) != 1) {
            fclose(f);
            return false;
        }
        
        documents = new Document[num_docs];
        for (uint32_t i = 0; i < num_docs; i++) {
            documents[i].url = nullptr;
            documents[i].title = nullptr;
        }
        
        for (uint32_t i = 0; i < num_docs; i++) {
            if (fread(&documents[i].doc_id, 4, 1, f) != 1) goto error;
            if (fread(&documents[i].url_length, 2, 1, f) != 1) goto error;
            
            documents[i].url = (char*)malloc(documents[i].url_length + 1);
            if (fread(documents[i].url, 1, documents[i].url_length, f) != documents[i].url_length) goto error;
            documents[i].url[documents[i].url_length] = '\0';
            
            if (fread(&documents[i].title_length, 2, 1, f) != 1) goto error;
            documents[i].title = (char*)malloc(documents[i].title_length + 1);
            if (fread(documents[i].title, 1, documents[i].title_length, f) != documents[i].title_length) goto error;
            documents[i].title[documents[i].title_length] = '\0';
            
            if (fread(&documents[i].content_length, 4, 1, f) != 1) goto error;
            if (fread(&documents[i].token_count, 4, 1, f) != 1) goto error;
            if (fread(&documents[i].unique_terms, 4, 1, f) != 1) goto error;
        }
        
        fclose(f);
        return true;
        
    error:
        fclose(f);
        return false;
    }
    
    bool load_inverted_index(const char* path) {
        FILE* f = fopen(path, "rb");
        if (!f) return false;
        
        uint32_t num_terms, reserved;
        if (fread(&num_terms, 4, 1, f) != 1 || fread(&reserved, 4, 1, f) != 1) {
            fclose(f);
            return false;
        }
        
        terms = new Term[num_terms];
        for (uint32_t i = 0; i < num_terms; i++) {
            terms[i].term = nullptr;
            terms[i].doc_ids = nullptr;
        }
        
        for (uint32_t i = 0; i < num_terms; i++) {
            if (fread(&terms[i].term_length, 2, 1, f) != 1) goto error;
            
            terms[i].term = (char*)malloc(terms[i].term_length + 1);
            if (fread(terms[i].term, 1, terms[i].term_length, f) != terms[i].term_length) goto error;
            terms[i].term[terms[i].term_length] = '\0';
            
            if (fread(&terms[i].document_frequency, 4, 1, f) != 1) goto error;
            
            terms[i].doc_ids = (uint32_t*)malloc(terms[i].document_frequency * sizeof(uint32_t));
            if (fread(terms[i].doc_ids, 4, terms[i].document_frequency, f) != terms[i].document_frequency) goto error;
        }
        
        fclose(f);
        return true;
        
    error:
        fclose(f);
        return false;
    }
};

DynamicArray<uint32_t> intersect_postings(const uint32_t* list1, uint32_t size1,
                                           const uint32_t* list2, uint32_t size2) {
    DynamicArray<uint32_t> result;
    uint32_t i = 0, j = 0;
    
    while (i < size1 && j < size2) {
        if (list1[i] == list2[j]) {
            result.push_back(list1[i]);
            i++;
            j++;
        } else if (list1[i] < list2[j]) {
            i++;
        } else {
            j++;
        }
    }
    
    return result;
}

DynamicArray<uint32_t> union_postings(const uint32_t* list1, uint32_t size1,
                                       const uint32_t* list2, uint32_t size2) {
    DynamicArray<uint32_t> result;
    uint32_t i = 0, j = 0;
    
    while (i < size1 && j < size2) {
        if (list1[i] == list2[j]) {
            result.push_back(list1[i]);
            i++;
            j++;
        } else if (list1[i] < list2[j]) {
            result.push_back(list1[i]);
            i++;
        } else {
            result.push_back(list2[j]);
            j++;
        }
    }
    
    while (i < size1) result.push_back(list1[i++]);
    while (j < size2) result.push_back(list2[j++]);
    
    return result;
}

DynamicArray<uint32_t> negate_postings(const uint32_t* list, uint32_t size,
                                        uint32_t total_docs) {
    DynamicArray<uint32_t> result;
    uint32_t j = 0;
    
    for (uint32_t doc_id = 1; doc_id <= total_docs; doc_id++) {
        if (j < size && list[j] == doc_id) {
            j++;
        } else {
            result.push_back(doc_id);
        }
    }
    
    return result;
}

enum TokenType {
    TOKEN_WORD,
    TOKEN_AND,
    TOKEN_OR,
    TOKEN_NOT,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
    TOKEN_END
};

struct QueryToken {
    TokenType type;
    char word[256];
};

class BooleanQueryParser {
private:
    const char* query;
    size_t pos;
    
    void skip_whitespace() {
        while (query[pos] && isspace(query[pos])) {
            pos++;
        }
    }
    
    void to_lowercase(char* str) {
        for (int i = 0; str[i]; i++) {
            if (str[i] >= 'A' && str[i] <= 'Z') {
                str[i] = str[i] - 'A' + 'a';
            }
        }
    }
    
public:
    BooleanQueryParser(const char* q) : query(q), pos(0) {}
    
    QueryToken next_token() {
        skip_whitespace();
        
        QueryToken token;
        token.word[0] = '\0';
        
        if (!query[pos]) {
            token.type = TOKEN_END;
            return token;
        }
        
        if (query[pos] == '(') {
            token.type = TOKEN_LPAREN;
            pos++;
            return token;
        }
        
        if (query[pos] == ')') {
            token.type = TOKEN_RPAREN;
            pos++;
            return token;
        }
        
        if (query[pos] == '!') {
            token.type = TOKEN_NOT;
            pos++;
            return token;
        }
        
        if (query[pos] == '|' && query[pos+1] == '|') {
            token.type = TOKEN_OR;
            pos += 2;
            return token;
        }
        
        if (query[pos] == '&' && query[pos+1] == '&') {
            token.type = TOKEN_AND;
            pos += 2;
            return token;
        }
        
        int i = 0;
        while (query[pos] && (isalnum(query[pos]) || query[pos] == '-' || 
                              query[pos] == '\'' || (unsigned char)query[pos] >= 128)) {
            if (i < 255) {
                token.word[i++] = query[pos];
            }
            pos++;
        }
        token.word[i] = '\0';
        
        if (i > 0) {
            to_lowercase(token.word);
            token.type = TOKEN_WORD;
        } else {
            pos++;
            return next_token();
        }
        
        return token;
    }
    
    void reset() {
        pos = 0;
    }
};

#endif // SEARCHER_H

