#ifndef INDEXER_H
#define INDEXER_H

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cstdlib>

#define INDEX_MAGIC 0x49444558
#define INDEX_VERSION 0x0001
#define FLAG_COMPRESSED  0x0001
#define FLAG_STEMMED     0x0002
#define FLAG_POSITIONAL  0x0004

struct IndexOptions {
    bool use_stemming;
    
    IndexOptions() : use_stemming(false) {}
};

struct IndexMetadata {
    uint32_t magic;
    uint16_t version;
    uint16_t flags;
    uint32_t total_documents;
    uint32_t total_unique_terms;
    uint64_t timestamp;
    uint32_t forward_offset;
    uint32_t forward_size;
    uint32_t inverted_offset;
    uint32_t inverted_size;
    char reserved[256];
};

struct Document {
    uint32_t doc_id;
    char* url;
    uint16_t url_length;
    char* title;
    uint16_t title_length;
    uint32_t content_length;
    uint32_t token_count;
    uint32_t unique_terms;
};

struct Term {
    char* term;
    uint16_t term_length;
    uint32_t document_frequency;
    uint32_t* doc_ids;
};

template<typename T>
struct DynamicArray {
    T* data;
    size_t size;
    size_t capacity;
    
    DynamicArray() : data(nullptr), size(0), capacity(0) {}
    
    DynamicArray(const DynamicArray& other) : data(nullptr), size(0), capacity(0) {
        if (other.size > 0) {
            reserve(other.capacity);
            for (size_t i = 0; i < other.size; i++) {
                push_back(other.data[i]);
            }
        }
    }
    
    DynamicArray& operator=(const DynamicArray& other) {
        if (this != &other) {
            if (data) delete[] data;
            data = nullptr;
            size = 0;
            capacity = 0;
            
            if (other.size > 0) {
                reserve(other.capacity);
                for (size_t i = 0; i < other.size; i++) {
                    push_back(other.data[i]);
                }
            }
        }
        return *this;
    }
    
    ~DynamicArray() {
        if (data) delete[] data;
    }
    
    void reserve(size_t new_capacity) {
        if (new_capacity <= capacity) return;
        
        T* new_data = new T[new_capacity];
        for (size_t i = 0; i < size; i++) {
            new_data[i] = data[i];
        }
        
        if (data) delete[] data;
        data = new_data;
        capacity = new_capacity;
    }
    
    void push_back(const T& value) {
        if (size >= capacity) {
            reserve(capacity == 0 ? 8 : capacity * 2);
        }
        data[size++] = value;
    }
    
    T& operator[](size_t index) {
        return data[index];
    }
    
    const T& operator[](size_t index) const {
        return data[index];
    }
};

struct HashNode {
    char* key;
    DynamicArray<uint32_t>* doc_ids;
    HashNode* next;
    
    HashNode(const char* k) : key(nullptr), doc_ids(nullptr), next(nullptr) {
        size_t len = 0;
        while (k[len]) len++;
        key = new char[len + 1];
        for (size_t i = 0; i <= len; i++) {
            key[i] = k[i];
        }
        doc_ids = new DynamicArray<uint32_t>();
    }
    
    ~HashNode() {
        if (key) delete[] key;
        if (doc_ids) delete doc_ids;
    }
};

class HashMap {
private:
    HashNode** buckets;
    size_t bucket_count;
    size_t item_count;
    
    size_t hash(const char* str) const {
        size_t h = 5381;
        int c;
        while ((c = *str++)) {
            h = ((h << 5) + h) + c;
        }
        return h % bucket_count;
    }
    
public:
    HashMap(size_t num_buckets = 10000) 
        : bucket_count(num_buckets), item_count(0) {
        buckets = new HashNode*[bucket_count];
        for (size_t i = 0; i < bucket_count; i++) {
            buckets[i] = nullptr;
        }
    }
    
    ~HashMap() {
        for (size_t i = 0; i < bucket_count; i++) {
            HashNode* node = buckets[i];
            while (node) {
                HashNode* next = node->next;
                delete node;
                node = next;
            }
        }
        delete[] buckets;
    }
    
    DynamicArray<uint32_t>* get_or_create(const char* key) {
        size_t idx = hash(key);
        HashNode* node = buckets[idx];
        
        while (node) {
            if (strcmp(node->key, key) == 0) {
                return node->doc_ids;
            }
            node = node->next;
        }
        
        HashNode* new_node = new HashNode(key);
        new_node->next = buckets[idx];
        buckets[idx] = new_node;
        item_count++;
        
        return new_node->doc_ids;
    }
    
    size_t size() const { return item_count; }
    
    class Iterator {
    private:
        HashMap* map;
        size_t bucket_idx;
        HashNode* current;
        
    public:
        Iterator(HashMap* m) : map(m), bucket_idx(0), current(nullptr) {
            while (bucket_idx < map->bucket_count && !map->buckets[bucket_idx]) {
                bucket_idx++;
            }
            if (bucket_idx < map->bucket_count) {
                current = map->buckets[bucket_idx];
            }
        }
        
        bool has_next() const {
            return current != nullptr;
        }
        
        HashNode* next() {
            if (!current) return nullptr;
            
            HashNode* result = current;
            current = current->next;
            
            if (!current) {
                bucket_idx++;
                while (bucket_idx < map->bucket_count && !map->buckets[bucket_idx]) {
                    bucket_idx++;
                }
                if (bucket_idx < map->bucket_count) {
                    current = map->buckets[bucket_idx];
                }
            }
            
            return result;
        }
    };
    
    Iterator get_iterator() {
        return Iterator(this);
    }
};

class Indexer {
private:
    DynamicArray<Document> documents;
    HashMap inverted_index;
    IndexMetadata metadata;
    IndexOptions options;
    
    void to_lowercase(char* str);
    bool is_valid_term(const char* term);
    
public:
    Indexer();
    ~Indexer();
    
    void set_options(const IndexOptions& opts);
    bool is_using_stemming() const;
    void add_document(uint32_t doc_id, const char* url, const char* title, const char* content);
    void tokenize_and_index(uint32_t doc_id, const char* text);
    void sort_index();
    bool save_to_file(const char* base_path);
    bool load_from_file(const char* base_path);
    void print_statistics() const;
    DynamicArray<uint32_t>* search_term(const char* term);
};

#endif // INDEXER_H

