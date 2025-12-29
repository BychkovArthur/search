#ifndef TURKISH_STEMMER_H
#define TURKISH_STEMMER_H

#include <cstring>
#include <cstdint>

class TurkishStemmer {
private:
    static bool ends_with(const char* word, const char* suffix) {
        size_t word_len = strlen(word);
        size_t suffix_len = strlen(suffix);
        
        if (word_len < suffix_len) return false;
        
        return strcmp(word + word_len - suffix_len, suffix) == 0;
    }
    
    static void remove_suffix(char* word, const char* suffix) {
        size_t word_len = strlen(word);
        size_t suffix_len = strlen(suffix);
        word[word_len - suffix_len] = '\0';
    }
    
public:
    static bool stem(char* word) {
        size_t len = strlen(word);
        
        if (len < 5) return false;
        
        bool modified = false;
        
        if (ends_with(word, "lar") || ends_with(word, "ler")) {
            remove_suffix(word, ends_with(word, "lar") ? "lar" : "ler");
            modified = true;
            len = strlen(word);
        }
        
        if (len >= 4) {
            if (ends_with(word, "im") || ends_with(word, "in") || 
                ends_with(word, "um") || ends_with(word, "un")) {
                remove_suffix(word, "im");
                modified = true;
                len = strlen(word);
            }
        }
        
        if (len >= 4) {
            const char* case_suffixes[] = {
                "nda", "nde", "dan", "den", "nin", "nun", "nan", 
                "nen", "yi", "yu", "ya", "ye", "da", "de", "ta", "te",
                nullptr
            };
            
            for (int i = 0; case_suffixes[i]; i++) {
                if (ends_with(word, case_suffixes[i])) {
                    remove_suffix(word, case_suffixes[i]);
                    modified = true;
                    break;
                }
            }
        }
        
        return modified;
    }
    
    static void stem_aggressive(char* word) {
        for (int i = 0; i < 3; i++) {
            if (!stem(word)) break;
        }
    }
    
    static void get_stem(const char* word, char* stem_buffer, size_t buffer_size) {
        strncpy(stem_buffer, word, buffer_size - 1);
        stem_buffer[buffer_size - 1] = '\0';
        stem(stem_buffer);
    }
};

#endif // TURKISH_STEMMER_H

