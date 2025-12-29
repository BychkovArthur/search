/*
 * Токенизатор для турецкого языка
 * Система информационного поиска - Токенизация
 * 
 * Примечание: STL разрешен для токенизации согласно требованиям
 * Для остальных компонент (индексы и т.д.) STL запрещен
 */

#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <chrono>
#include <iomanip>

using namespace std;

class TurkishTokenizer {
private:
    long long total_tokens;
    long long total_chars;
    long long total_bytes;
    
    // Проверка турецких UTF-8 букв
    bool is_turkish_letter(unsigned char c1, unsigned char c2) {
        if (c1 == 0xC3) { // ç, ğ, ı, ö, ü
            return (c2 == 0xA7 || c2 == 0x87 || // ç Ç
                    c2 == 0x9F || c2 == 0x9E || // ğ Ğ  
                    c2 == 0xB1 ||               // ı
                    c2 == 0xB6 || c2 == 0x96 || // ö Ö
                    c2 == 0xBC || c2 == 0x9C);  // ü Ü
        }
        if (c1 == 0xC5) { // ş, İ
            return (c2 == 0x9F || c2 == 0x9E || // ş Ş
                    c2 == 0xB1 || c2 == 0xB0);  // ı İ
        }
        return false;
    }
    
    bool is_letter_at(const string& text, size_t& pos) {
        if (pos >= text.length()) return false;
        
        unsigned char c = text[pos];
        
        // ASCII буквы
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) {
            pos++;
            return true;
        }
        
        // UTF-8 многобайтовые символы
        if (c >= 0xC0 && c < 0xF5) {
            // Турецкие или другие UTF-8 буквы
            if (pos + 1 < text.length()) {
                if (is_turkish_letter(c, text[pos + 1])) {
                    pos += 2;
                    return true;
                }
                // Другие двухбайтовые UTF-8 символы (считаем буквами)
                if (c < 0xE0) {
                    pos += 2;
                    return true;
                }
                // Трехбайтовые UTF-8
                if (c < 0xF0 && pos + 2 < text.length()) {
                    pos += 3;
                    return true;
                }
            }
        }
        
        return false;
    }
    
    bool is_digit(char c) {
        return c >= '0' && c <= '9';
    }
    
    string to_lowercase(const string& token) {
        string result = token;
        for (size_t i = 0; i < result.length(); i++) {
            if (result[i] >= 'A' && result[i] <= 'Z') {
                result[i] = result[i] + 32;
            }
        }
        return result;
    }

public:
    TurkishTokenizer() : total_tokens(0), total_chars(0), total_bytes(0) {}
    
    // Токенизация текста
    vector<string> tokenize(const string& text) {
        vector<string> tokens;
        size_t pos = 0;
        total_bytes += text.length();
        
        while (pos < text.length()) {
            // Пропуск пробелов
            while (pos < text.length() && (text[pos] == ' ' || text[pos] == '\t' || 
                   text[pos] == '\n' || text[pos] == '\r')) {
                pos++;
            }
            
            if (pos >= text.length()) break;
            
            size_t start = pos;
            size_t temp_pos = pos;
            
            // Слова (буквы)
            if (is_letter_at(text, temp_pos)) {
                start = pos;
                pos = temp_pos;
                
                while (pos < text.length()) {
                    temp_pos = pos;
                    
                    if (is_letter_at(text, temp_pos)) {
                        pos = temp_pos;
                        continue;
                    }
                    
                    // Апостроф в слове (Ali'nin)
                    if (text[pos] == '\'' && pos + 1 < text.length()) {
                        size_t next = pos + 1;
                        if (is_letter_at(text, next)) {
                            pos = next;
                            continue;
                        }
                    }
                    
                    // Дефис в составном слове
                    if (text[pos] == '-' && pos + 1 < text.length()) {
                        size_t next = pos + 1;
                        if (is_letter_at(text, next)) {
                            pos = next;
                            continue;
                        }
                    }
                    
                    break;
                }
                
                string token = text.substr(start, pos - start);
                token = to_lowercase(token);
                tokens.push_back(token);
                total_tokens++;
                total_chars += token.length();
                continue;
            }
            
            // Числа
            if (is_digit(text[pos])) {
                start = pos;
                while (pos < text.length() && (is_digit(text[pos]) || text[pos] == '.')) {
                    pos++;
                }
                string token = text.substr(start, pos - start);
                tokens.push_back(token);
                total_tokens++;
                total_chars += token.length();
                continue;
            }
            
            // Пропуск других символов (пунктуация игнорируется)
            pos++;
        }
        
        return tokens;
    }
    
    // Статистика
    long long get_token_count() const { return total_tokens; }
    long long get_total_chars() const { return total_chars; }
    long long get_bytes_processed() const { return total_bytes; }
    
    double get_avg_token_length() const {
        return total_tokens > 0 ? (double)total_chars / total_tokens : 0.0;
    }
    
    void print_stats() const {
        cerr << "\n=== Статистика токенизации ===\n";
        cerr << "Токенов: " << total_tokens << "\n";
        cerr << "Символов в токенах: " << total_chars << "\n";
        cerr << "Средняя длина токена: " << fixed << setprecision(2) 
             << get_avg_token_length() << " символов\n";
        cerr << "Обработано байт: " << total_bytes << "\n";
    }
};

int main(int argc, char* argv[]) {
    TurkishTokenizer tokenizer;
    
    // Режим: stdin -> stdout (для CLI утилиты)
    string line;
    auto start_time = chrono::high_resolution_clock::now();
    
    while (getline(cin, line)) {
        vector<string> tokens = tokenizer.tokenize(line);
        
        // Вывод токенов (один токен на строку для удобства обработки)
        for (const auto& token : tokens) {
            cout << token << "\n";
        }
    }
    
    auto end_time = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::microseconds>(end_time - start_time);
    
    // Статистика в stderr
    tokenizer.print_stats();
    
    double seconds = duration.count() / 1000000.0;
    double kb_per_sec = (tokenizer.get_bytes_processed() / 1024.0) / seconds;
    
    cerr << "Время: " << fixed << setprecision(3) << seconds << " сек\n";
    cerr << "Скорость: " << fixed << setprecision(2) << kb_per_sec << " КБ/сек\n";
    
    return 0;
}
