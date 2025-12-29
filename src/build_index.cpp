#include "indexer.h"
#include <cstdio>
#include <cstring>
#include <ctime>
#include <sys/time.h>

bool parse_tsv_line(const char* line, uint32_t& doc_id, char* url, char* title, char* content) {
    const char* p = line;
    
    doc_id = atoi(p);
    
    while (*p && *p != '\t') p++;
    if (!*p) return false;
    p++;
    
    int i = 0;
    while (*p && *p != '\t' && i < 511) {
        url[i++] = *p++;
    }
    url[i] = '\0';
    if (!*p) return false;
    p++;
    
    i = 0;
    while (*p && *p != '\t' && i < 511) {
        title[i++] = *p++;
    }
    title[i] = '\0';
    if (!*p) return false;
    p++;
    
    i = 0;
    while (*p && *p != '\n' && *p != '\r' && i < 99999) {
        content[i++] = *p++;
    }
    content[i] = '\0';
    
    return doc_id > 0 && url[0] && content[0];
}

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        printf("Использование: %s <input.tsv> <output_index_base> [--stemming]\n", argv[0]);
        printf("\nПример:\n");
        printf("  %s indexer_input.tsv index\n", argv[0]);
        printf("  %s indexer_input.tsv index_stemmed --stemming\n", argv[0]);
        printf("\nОпции:\n");
        printf("  --stemming  Включить стемминг (ЛР5)\n");
        printf("\nСоздаст файлы: <output>.meta, <output>.forward, <output>.inverted\n");
        return 1;
    }
    
    const char* input_file = argv[1];
    const char* output_base = argv[2];
    bool use_stemming = false;
    
    for (int i = 3; i < argc; i++) {
        if (strcmp(argv[i], "--stemming") == 0) {
            use_stemming = true;
        }
    }
    
    printf("=== ПОСТРОЕНИЕ ИНДЕКСА ===\n");
    printf("Входной файл: %s\n", input_file);
    printf("Базовое имя индекса: %s\n", output_base);
    printf("Стемминг: %s\n\n", use_stemming ? "ВКЛ" : "ВЫКЛ");
    
    FILE* f = fopen(input_file, "r");
    if (!f) {
        fprintf(stderr, "Ошибка открытия файла: %s\n", input_file);
        return 1;
    }
    
    Indexer indexer;
    
    if (use_stemming) {
        IndexOptions opts;
        opts.use_stemming = true;
        indexer.set_options(opts);
    }
    
    char line[200000];
    char url[512], title[512];
    char* content = new char[100000];
    uint32_t doc_id;
    
    int processed = 0;
    int errors = 0;
    
    double start_time = get_time();
    double last_report = start_time;
    
    printf("Чтение и индексация документов...\n");
    
    while (fgets(line, sizeof(line), f)) {
        if (parse_tsv_line(line, doc_id, url, title, content)) {
            indexer.add_document(doc_id, url, title, content);
            processed++;
            
            // Периодический отчет
            double now = get_time();
            if (now - last_report >= 1.0) {  // Каждую секунду
                double elapsed = now - start_time;
                double docs_per_sec = processed / elapsed;
                printf("\r  Обработано: %d документов (%.1f док/сек)", 
                       processed, docs_per_sec);
                fflush(stdout);
                last_report = now;
            }
        } else {
            errors++;
        }
    }
    
    double parse_time = get_time() - start_time;
    printf("\n\nОбработано документов: %d\n", processed);
    printf("Ошибок парсинга: %d\n", errors);
    printf("Время обработки: %.2f сек\n", parse_time);
    printf("Скорость: %.1f док/сек\n\n", processed / parse_time);
    
    fclose(f);
    delete[] content;
    
    printf("Сортировка индекса...\n");
    double sort_start = get_time();
    indexer.sort_index();
    double sort_time = get_time() - sort_start;
    printf("Время сортировки: %.2f сек\n\n", sort_time);
    
    indexer.print_statistics();
    
    printf("Сохранение индекса...\n");
    double save_start = get_time();
    if (!indexer.save_to_file(output_base)) {
        fprintf(stderr, "Ошибка сохранения индекса\n");
        return 1;
    }
    double save_time = get_time() - save_start;
    printf("Время сохранения: %.2f сек\n\n", save_time);
    
    double total_time = get_time() - start_time;
    printf("=== ИТОГО ===\n");
    printf("Общее время: %.2f сек\n", total_time);
    printf("  Парсинг и индексация: %.2f сек (%.1f%%)\n", 
           parse_time, parse_time / total_time * 100);
    printf("  Сортировка: %.2f сек (%.1f%%)\n", 
           sort_time, sort_time / total_time * 100);
    printf("  Сохранение: %.2f сек (%.1f%%)\n", 
           save_time, save_time / total_time * 100);
    printf("\nСкорость индексации:\n");
    printf("  %.1f документов/сек\n", processed / total_time);
    printf("  %.1f документов/мин\n", processed / total_time * 60);
    
    printf("\nИндекс построен успешно!\n");
    
    return 0;
}

