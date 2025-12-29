// dump_index.cpp
// Утилита для вывода содержимого индекса

#include "indexer.h"
#include <cstdio>

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Использование: %s <index_base>\n", argv[0]);
        return 1;
    }
    
    const char* base_path = argv[1];
    char path[512];
    
    // Загрузка inverted index напрямую
    snprintf(path, sizeof(path), "%s.inverted", base_path);
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "Ошибка открытия: %s\n", path);
        return 1;
    }
    
    // Читаем заголовок
    uint32_t num_terms, reserved;
    if (fread(&num_terms, 4, 1, f) != 1) {
        fprintf(stderr, "Ошибка чтения num_terms\n");
        fclose(f);
        return 1;
    }
    if (fread(&reserved, 4, 1, f) != 1) {
        fprintf(stderr, "Ошибка чтения reserved\n");
        fclose(f);
        return 1;
    }
    
    printf("Всего термов: %u\n\n", num_terms);
    printf("Первые 100 термов:\n");
    printf("%-40s %10s\n", "Терм", "DF");
    printf("%s\n", "-------------------------------------------------------------");
    
    // Читаем первые 100 термов
    for (uint32_t i = 0; i < num_terms && i < 100; i++) {
        uint16_t term_length;
        if (fread(&term_length, 2, 1, f) != 1) break;
        
        char term[257];
        if (fread(term, 1, term_length, f) != term_length) break;
        term[term_length] = '\0';
        
        uint32_t df;
        if (fread(&df, 4, 1, f) != 1) break;
        
        printf("%-40s %10u\n", term, df);
        
        // Пропускаем doc IDs
        fseek(f, df * 4, SEEK_CUR);
    }
    
    fclose(f);
    return 0;
}

