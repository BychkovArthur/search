// test_stemmer.cpp
// Тестирование турецкого стеммера

#include "turkish_stemmer.h"
#include <cstdio>
#include <cstring>

void test_stemmer(const char* word) {
    char stemmed[256];
    strcpy(stemmed, word);
    
    bool modified = TurkishStemmer::stem(stemmed);
    
    printf("%-30s → %-30s %s\n", word, stemmed, modified ? "OK" : "");
}

int main() {
    printf("=== Тестирование турецкого стеммера ===\n\n");
    
    printf("Множественное число:\n");
    test_stemmer("kitap");        // книга (без изменений)
    test_stemmer("kitaplar");     // книги → kitap
    test_stemmer("evler");        // дома → ev
    test_stemmer("arabalar");     // машины → araba
    printf("\n");
    
    printf("Притяжательные:\n");
    test_stemmer("evim");         // мой дом → ev
    test_stemmer("evin");         // твой дом → ev
    test_stemmer("kitabım");      // моя книга → kitab
    printf("\n");
    
    printf("Падежи:\n");
    test_stemmer("evde");         // в доме → ev
    test_stemmer("evden");        // из дома → ev
    test_stemmer("istanbul");     // Стамбул (без изменений)
    test_stemmer("istanbulda");   // в Стамбуле → istanbul
    test_stemmer("istanbuldan");  // из Стамбула → istanbul
    printf("\n");
    
    printf("Комбинации:\n");
    test_stemmer("evlerde");      // в домах → ev (ler+de)
    test_stemmer("kitaplardan");  // из книг → kitap (lar+dan)
    printf("\n");
    
    printf("Короткие слова (не стеммятся):\n");
    test_stemmer("ev");           // дом
    test_stemmer("bu");           // это
    test_stemmer("ve");           // и
    printf("\n");
    
    printf("Реальные примеры:\n");
    test_stemmer("osmanlı");
    test_stemmer("osmanlılar");   // османы → osmanlı
    test_stemmer("türkiye");
    test_stemmer("türkiyede");    // в Турции → türkiye
    test_stemmer("tarih");
    test_stemmer("tarihinde");    // в истории → tarih
    test_stemmer("savaş");
    test_stemmer("savaşlar");     // войны → savaş
    
    return 0;
}

