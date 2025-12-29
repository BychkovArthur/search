#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import math
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

def read_tokens(filename):
    tokens = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            tokens.extend(line.strip().split())
    return tokens

def zipf_law(rank, c):
    return c / rank

def mandelbrot_law(rank, a, b, c):
    return c / ((rank + b) ** a)

def analyze_zipf(tokens_file, output_prefix='zipf'):
    
    print("=" * 70)
    print("АНАЛИЗ ЗАКОНА ЦИПФА")
    print("=" * 70)
    
    print(f"\nЧтение токенов из {tokens_file}...")
    tokens = read_tokens(tokens_file)
    print(f"Всего токенов: {len(tokens):,}")
    
    print("Подсчет частот...")
    freq = Counter(tokens)
    print(f"Уникальных токенов: {len(freq):,}")
    
    sorted_freqs = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 70)
    print("ТОП-20 НАИБОЛЕЕ ЧАСТОТНЫХ ТОКЕНОВ")
    print("=" * 70)
    print(f"{'Ранг':<6} {'Токен':<20} {'Частота':<10} {'Доля,%'}")
    print("-" * 70)
    total_tokens = len(tokens)
    for i, (token, count) in enumerate(sorted_freqs[:20], 1):
        percentage = (count / total_tokens) * 100
        print(f"{i:<6} {token:<20} {count:<10,} {percentage:.3f}%")
    
    ranks = np.arange(1, len(sorted_freqs) + 1)
    frequencies = np.array([count for _, count in sorted_freqs])
    
    mask = frequencies > 0
    ranks_filtered = ranks[mask]
    frequencies_filtered = frequencies[mask]
    
    log_ranks = np.log10(ranks_filtered)
    log_frequencies = np.log10(frequencies_filtered)
    
    print("\n" + "=" * 70)
    print("ПОДГОНКА ЗАКОНА ЦИПФА")
    print("=" * 70)
    
    fit_limit = min(10000, len(ranks_filtered))
    
    try:
        popt_zipf, _ = curve_fit(zipf_law, ranks_filtered[:fit_limit], 
                                  frequencies_filtered[:fit_limit])
        C_zipf = popt_zipf[0]
        print(f"Константа C (закон Ципфа): {C_zipf:.2f}")
        
        predicted_zipf = zipf_law(ranks_filtered, C_zipf)
    except Exception as e:
        print(f"Ошибка при подгонке закона Ципфа: {e}")
        C_zipf = frequencies_filtered[0]
        predicted_zipf = zipf_law(ranks_filtered, C_zipf)
    
    print("\n" + "=" * 70)
    print("ПОДГОНКА ЗАКОНА МАНДЕЛЬБРОТА (опционально)")
    print("=" * 70)
    
    try:
        p0 = [1.0, 2.7, C_zipf]
        popt_mandel, _ = curve_fit(mandelbrot_law, ranks_filtered[:fit_limit], 
                                    frequencies_filtered[:fit_limit], p0=p0, 
                                    maxfev=10000)
        a_mandel, b_mandel, c_mandel = popt_mandel
        print(f"Параметры закона Мандельброта:")
        print(f"  a = {a_mandel:.4f}")
        print(f"  b = {b_mandel:.4f}")
        print(f"  C = {c_mandel:.2f}")
        
        predicted_mandel = mandelbrot_law(ranks_filtered, a_mandel, b_mandel, c_mandel)
        has_mandelbrot = True
    except Exception as e:
        print(f"Не удалось подогнать закон Мандельброта: {e}")
        has_mandelbrot = False
    
    print("\n" + "=" * 70)
    print("АНАЛИЗ РАСХОЖДЕНИЙ")
    print("=" * 70)
    
    mse_zipf = np.mean((frequencies_filtered - predicted_zipf) ** 2)
    print(f"MSE (Закон Ципфа): {mse_zipf:.2f}")
    
    if has_mandelbrot:
        mse_mandel = np.mean((frequencies_filtered - predicted_mandel) ** 2)
        print(f"MSE (Закон Мандельброта): {mse_mandel:.2f}")
    
    print("\n" + "=" * 70)
    print("ПОСТРОЕНИЕ ГРАФИКОВ")
    print("=" * 70)
    
    plt.figure(figsize=(14, 10))
    
    plt.subplot(2, 2, 1)
    plt.loglog(ranks_filtered, frequencies_filtered, 'b.', alpha=0.5, 
               markersize=2, label='Реальные данные')
    plt.loglog(ranks_filtered, predicted_zipf, 'r-', linewidth=2, 
               label=f'Закон Ципфа (C={C_zipf:.2f})')
    if has_mandelbrot:
        plt.loglog(ranks_filtered, predicted_mandel, 'g--', linewidth=2, 
                   label=f'Закон Мандельброта\n(a={a_mandel:.2f}, b={b_mandel:.2f}, C={c_mandel:.2f})')
    plt.xlabel('Ранг (логарифмическая шкала)', fontsize=12)
    plt.ylabel('Частота (логарифмическая шкала)', fontsize=12)
    plt.title('Закон Ципфа: логарифмическая шкала', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    limit = min(100, len(ranks_filtered))
    plt.plot(ranks_filtered[:limit], frequencies_filtered[:limit], 'b.-', 
             alpha=0.7, label='Реальные данные')
    plt.plot(ranks_filtered[:limit], predicted_zipf[:limit], 'r-', 
             linewidth=2, label='Закон Ципфа')
    if has_mandelbrot:
        plt.plot(ranks_filtered[:limit], predicted_mandel[:limit], 'g--', 
                 linewidth=2, label='Закон Мандельброта')
    plt.xlabel('Ранг', fontsize=12)
    plt.ylabel('Частота', fontsize=12)
    plt.title('Первые 100 токенов', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 3)
    relative_error_zipf = np.abs(frequencies_filtered - predicted_zipf) / frequencies_filtered * 100
    plt.semilogx(ranks_filtered, relative_error_zipf, 'r.', alpha=0.3, markersize=2)
    plt.xlabel('Ранг (логарифмическая шкала)', fontsize=12)
    plt.ylabel('Относительная ошибка, %', fontsize=12)
    plt.title('Относительное отклонение от закона Ципфа', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 4)
    freq_distribution = Counter(frequencies_filtered)
    freq_values = sorted(freq_distribution.keys())
    freq_counts = [freq_distribution[f] for f in freq_values]
    plt.loglog(freq_values, freq_counts, 'b.-', alpha=0.7)
    plt.xlabel('Частота появления', fontsize=12)
    plt.ylabel('Количество токенов с такой частотой', fontsize=12)
    plt.title('Распределение частот', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = f"{output_prefix}_plot.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"OK График сохранен: {plot_file}")
    
    data_file = f"{output_prefix}_data.txt"
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write("# Анализ закона Ципфа\n")
        f.write(f"# Всего токенов: {len(tokens)}\n")
        f.write(f"# Уникальных токенов: {len(freq)}\n")
        f.write(f"# Константа C (Ципф): {C_zipf:.2f}\n")
        if has_mandelbrot:
            f.write(f"# Параметры Мандельброта: a={a_mandel:.4f}, b={b_mandel:.4f}, C={c_mandel:.2f}\n")
        f.write("\n")
        f.write("Ранг\tТокен\tЧастота\tЗакон_Ципфа\tОтносит_ошибка,%\n")
        for i, (token, count) in enumerate(sorted_freqs[:1000], 1):
            pred = C_zipf / i
            error = abs(count - pred) / count * 100 if count > 0 else 0
            f.write(f"{i}\t{token}\t{count}\t{pred:.2f}\t{error:.2f}\n")
    print(f"OK Данные сохранены: {data_file}")
    
    print("\n" + "=" * 70)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        tokens_file = "corpus_tokens.txt"
    else:
        tokens_file = sys.argv[1]
    
    output_prefix = "zipf_analysis"
    if len(sys.argv) >= 3:
        output_prefix = sys.argv[2]
    
    analyze_zipf(tokens_file, output_prefix)

if __name__ == '__main__':
    main()

