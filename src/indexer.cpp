#include "indexer.h"
#include "turkish_stemmer.h"
#include <cstring>
#include <cstdio>
#include <ctime>
#include <cctype>

Indexer::Indexer() : inverted_index(100000) {
    metadata.magic = INDEX_MAGIC;
    metadata.version = INDEX_VERSION;
    metadata.flags = 0;
    metadata.total_documents = 0;
    metadata.total_unique_terms = 0;
    metadata.timestamp = time(nullptr);
    memset(metadata.reserved, 0, sizeof(metadata.reserved));
}

Indexer::~Indexer() {
    for (size_t i = 0; i < documents.size; i++) {
        if (documents[i].url) delete[] documents[i].url;
        if (documents[i].title) delete[] documents[i].title;
    }
}

void Indexer::set_options(const IndexOptions& opts) {
    options = opts;
    if (options.use_stemming) {
        metadata.flags |= FLAG_STEMMED;
    }
}

bool Indexer::is_using_stemming() const {
    return options.use_stemming;
}

void Indexer::to_lowercase(char* str) {
    for (size_t i = 0; str[i]; i++) {
        unsigned char c = (unsigned char)str[i];
        
        if (c == 'I' || c == 0xC4) {
            if (c == 'I' && str[i+1] == (char)0xB0) {
                str[i] = (char)0xC4;
                str[i+1] = (char)0xB1;
                continue;
            }
        }
        
        if (c >= 'A' && c <= 'Z') {
            str[i] = c + 32;
        }
        else if (c >= 0xC0 && c <= 0xDE) {
            str[i] = c + 32;
        }
    }
}

bool Indexer::is_valid_term(const char* term) {
    if (!term || !term[0]) return false;
    
    size_t len = strlen(term);
    if (len < 2) return false;
    
    bool has_letter = false;
    for (size_t i = 0; i < len; i++) {
        if (isalpha((unsigned char)term[i])) {
            has_letter = true;
            break;
        }
    }
    
    return has_letter;
}

void Indexer::add_document(uint32_t doc_id, const char* url, const char* title, 
                          const char* content) {
    Document doc;
    doc.doc_id = doc_id;
    
    doc.url_length = strlen(url);
    doc.url = new char[doc.url_length + 1];
    strcpy(doc.url, url);
    
    doc.title_length = strlen(title);
    doc.title = new char[doc.title_length + 1];
    strcpy(doc.title, title);
    
    doc.content_length = strlen(content);
    doc.token_count = 0;
    doc.unique_terms = 0;
    
    documents.push_back(doc);
    
    tokenize_and_index(doc_id, content);
    tokenize_and_index(doc_id, title);
    
    metadata.total_documents++;
}

void Indexer::tokenize_and_index(uint32_t doc_id, const char* text) {
    if (!text) return;
    
    char token[256];
    int token_pos = 0;
    bool in_token = false;
    
    for (size_t i = 0; text[i]; i++) {
        unsigned char c = (unsigned char)text[i];
        
        if (isalnum(c) || c == '_' || c >= 0x80) {
            if (!in_token) {
                token_pos = 0;
                in_token = true;
            }
            if (token_pos < 255) {
                token[token_pos++] = text[i];
            }
        }
        else {
            if (in_token && token_pos > 0) {
                token[token_pos] = '\0';
                
                to_lowercase(token);
                
                if (options.use_stemming) {
                    TurkishStemmer::stem(token);
                }
                
                if (is_valid_term(token)) {
                    DynamicArray<uint32_t>* doc_list = inverted_index.get_or_create(token);
                    
                    bool already_added = false;
                    for (size_t j = 0; j < doc_list->size; j++) {
                        if ((*doc_list)[j] == doc_id) {
                            already_added = true;
                            break;
                        }
                    }
                    
                    if (!already_added) {
                        doc_list->push_back(doc_id);
                    }
                    
                    documents[documents.size - 1].token_count++;
                }
            }
            in_token = false;
            token_pos = 0;
        }
    }
    
    if (in_token && token_pos > 0) {
        token[token_pos] = '\0';
        to_lowercase(token);
        if (is_valid_term(token)) {
            DynamicArray<uint32_t>* doc_list = inverted_index.get_or_create(token);
            bool already_added = false;
            for (size_t j = 0; j < doc_list->size; j++) {
                if ((*doc_list)[j] == doc_id) {
                    already_added = true;
                    break;
                }
            }
            if (!already_added) {
                doc_list->push_back(doc_id);
            }
            documents[documents.size - 1].token_count++;
        }
    }
}

static int compare_uint32(const void* a, const void* b) {
    uint32_t va = *(const uint32_t*)a;
    uint32_t vb = *(const uint32_t*)b;
    return (va > vb) - (va < vb);
}

static int compare_terms(const void* a, const void* b) {
    const HashNode* na = *(const HashNode**)a;
    const HashNode* nb = *(const HashNode**)b;
    return strcmp(na->key, nb->key);
}

void Indexer::sort_index() {
    printf("Сортировка постинг-листов...\n");
    
    HashMap::Iterator it = inverted_index.get_iterator();
    
    while (it.has_next()) {
        HashNode* node = it.next();
        if (node && node->doc_ids && node->doc_ids->size > 0) {
            qsort(node->doc_ids->data, node->doc_ids->size, 
                  sizeof(uint32_t), compare_uint32);
        }
    }
    
    metadata.total_unique_terms = inverted_index.size();
    printf("Сортировка завершена. Уникальных термов: %u\n", 
           metadata.total_unique_terms);
}

bool Indexer::save_to_file(const char* base_path) {
    char meta_path[512], forward_path[512], inverted_path[512];
    snprintf(meta_path, sizeof(meta_path), "%s.meta", base_path);
    snprintf(forward_path, sizeof(forward_path), "%s.forward", base_path);
    snprintf(inverted_path, sizeof(inverted_path), "%s.inverted", base_path);
    
    printf("Сохранение индекса...\n");
    
    FILE* meta_file = fopen(meta_path, "wb");
    if (!meta_file) {
        fprintf(stderr, "Ошибка создания файла метаданных\n");
        return false;
    }
    
    fwrite(&metadata, sizeof(IndexMetadata), 1, meta_file);
    fclose(meta_file);
    
    FILE* forward_file = fopen(forward_path, "wb");
    if (!forward_file) {
        fprintf(stderr, "Ошибка создания файла прямого индекса\n");
        return false;
    }
    
    uint32_t num_docs = documents.size;
    fwrite(&num_docs, sizeof(uint32_t), 1, forward_file);
    fwrite(&num_docs, sizeof(uint32_t), 1, forward_file);
    
    for (size_t i = 0; i < documents.size; i++) {
        Document& doc = documents[i];
        fwrite(&doc.doc_id, sizeof(uint32_t), 1, forward_file);
        fwrite(&doc.url_length, sizeof(uint16_t), 1, forward_file);
        fwrite(doc.url, 1, doc.url_length, forward_file);
        fwrite(&doc.title_length, sizeof(uint16_t), 1, forward_file);
        fwrite(doc.title, 1, doc.title_length, forward_file);
        fwrite(&doc.content_length, sizeof(uint32_t), 1, forward_file);
        fwrite(&doc.token_count, sizeof(uint32_t), 1, forward_file);
        fwrite(&doc.unique_terms, sizeof(uint32_t), 1, forward_file);
    }
    
    fclose(forward_file);
    
    FILE* inverted_file = fopen(inverted_path, "wb");
    if (!inverted_file) {
        fprintf(stderr, "Ошибка создания файла инвертированного индекса\n");
        return false;
    }
    
    uint32_t num_terms = inverted_index.size();
    fwrite(&num_terms, sizeof(uint32_t), 1, inverted_file);
    fwrite(&num_terms, sizeof(uint32_t), 1, inverted_file);
    
    HashNode** term_array = new HashNode*[num_terms];
    uint32_t idx = 0;
    
    HashMap::Iterator it = inverted_index.get_iterator();
    while (it.has_next()) {
        HashNode* node = it.next();
        if (node) {
            term_array[idx++] = node;
        }
    }
    
    printf("Сортировка термов для сохранения...\n");
    qsort(term_array, num_terms, sizeof(HashNode*), compare_terms);
    
    for (uint32_t i = 0; i < num_terms; i++) {
        HashNode* node = term_array[i];
        uint16_t term_len = strlen(node->key);
        uint32_t df = node->doc_ids->size;
        
        fwrite(&term_len, sizeof(uint16_t), 1, inverted_file);
        fwrite(node->key, 1, term_len, inverted_file);
        fwrite(&df, sizeof(uint32_t), 1, inverted_file);
        fwrite(node->doc_ids->data, sizeof(uint32_t), df, inverted_file);
    }
    
    delete[] term_array;
    fclose(inverted_file);
    
    printf("Индекс сохранен успешно:\n");
    printf("  %s\n", meta_path);
    printf("  %s\n", forward_path);
    printf("  %s\n", inverted_path);
    
    return true;
}

void Indexer::print_statistics() const {
    printf("\n");
    printf("=== СТАТИСТИКА ИНДЕКСА ===\n");
    printf("Документов: %u\n", metadata.total_documents);
    printf("Уникальных термов: %u\n", metadata.total_unique_terms);
    printf("Версия формата: 0x%04X\n", metadata.version);
    printf("Флаги: 0x%04X\n", metadata.flags);
    printf("\n");
}

DynamicArray<uint32_t>* Indexer::search_term(const char* term) {
    char lowercase_term[256];
    strncpy(lowercase_term, term, 255);
    lowercase_term[255] = '\0';
    to_lowercase(lowercase_term);
    
    return inverted_index.get_or_create(lowercase_term);
}

