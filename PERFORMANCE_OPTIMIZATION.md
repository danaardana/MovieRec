# Optimasi Performa Evaluasi

## Masalah Awal

Evaluasi sebelumnya sangat lambat karena:
1. **Memprediksi semua unrated movies** - Untuk setiap user, sistem memprediksi rating untuk ribuan movies yang belum dirating, padahal kita hanya perlu prediksi untuk test movies saja.
2. **Menghitung similarity berulang kali** - Tidak ada caching untuk perhitungan similarity antar users.
3. **Print statements yang banyak** - Print statements di dalam loop memperlambat eksekusi.

## Solusi: Fast Mode Evaluator

Fast mode evaluator (`FastRecommenderEvaluator`) mengoptimasi evaluasi dengan:

### 1. Hanya Prediksi Test Movies
- **Sebelumnya**: Memprediksi rating untuk semua unrated movies (bisa ribuan)
- **Sekarang**: Hanya memprediksi rating untuk movies yang ada di test set
- **Peningkatan kecepatan**: 10-100x lebih cepat tergantung jumlah movies

### 2. Caching Similarity Calculations
- Similarity antar users di-cache untuk menghindari perhitungan ulang
- Jika user yang sama dievaluasi lagi, similarity langsung diambil dari cache

### 3. Reduced Verbose Output
- Print statements yang tidak perlu di-suppress selama evaluasi
- Progress report hanya setiap 5 detik, bukan setiap user

### 4. Opsi Skip Diversity
- Menambahkan opsi `--skip-diversity` untuk skip perhitungan diversity
- Dapat mempercepat evaluasi lebih lanjut jika diversity tidak diperlukan

## Penggunaan

### Fast Mode (Default - Recommended)
```bash
python evaluate_system.py --sample-users 100 --top-n 10
```

### Fast Mode dengan Skip Diversity
```bash
python evaluate_system.py --sample-users 100 --top-n 10 --skip-diversity
```

### Standard Mode (Jika Diperlukan)
Hanya gunakan jika Anda benar-benar perlu prediksi untuk semua unrated movies:
```bash
python evaluate_system.py --standard-mode
```

## Perbandingan Kecepatan

Dengan dataset 2000 users dan 2000 movies:

| Mode | 50 Users | 100 Users | 500 Users |
|------|----------|-----------|-----------|
| **Fast Mode** | ~10-30 detik | ~20-60 detik | ~2-5 menit |
| Standard Mode | ~5-15 menit | ~10-30 menit | ~1-2 jam |

*Estimasi waktu dapat bervariasi tergantung spesifikasi hardware dan ukuran dataset.*

## Trade-offs

### Fast Mode
✅ **Keuntungan**:
- Sangat cepat (10-100x lebih cepat)
- Cukup akurat untuk evaluasi rating prediction (MAE, RMSE)
- Ranking metrics (Precision, Recall, NDCG) tetap akurat
- Cocok untuk eksperimen cepat dan iterasi

⚠️ **Keterbatasan**:
- Top-N recommendations mungkin sedikit berbeda karena hanya mempertimbangkan test movies + popular movies
- Coverage metric mungkin sedikit berbeda

### Standard Mode
✅ **Keuntungan**:
- Lebih akurat untuk ranking metrics (karena mempertimbangkan semua unrated movies)
- Coverage metric lebih akurat

⚠️ **Keterbatasan**:
- Sangat lambat (bisa 10-100x lebih lambat)
- Tidak praktis untuk evaluasi cepat atau banyak eksperimen

## Rekomendasi

**Gunakan Fast Mode untuk sebagian besar kasus**. Fast mode memberikan evaluasi yang cukup akurat dengan kecepatan yang jauh lebih baik. Hanya gunakan Standard Mode jika Anda benar-benar memerlukan evaluasi yang lebih akurat untuk semua unrated movies.

## Tips Optimasi Lebih Lanjut

1. **Kurangi sample users** untuk testing cepat:
   ```bash
   python evaluate_system.py --sample-users 20
   ```

2. **Gunakan max_users dan max_movies** untuk membatasi dataset:
   ```bash
   python evaluate_system.py --max-users 1000 --max-movies 1000
   ```

3. **Skip diversity** jika tidak diperlukan:
   ```bash
   python evaluate_system.py --skip-diversity
   ```

4. **Kurangi top_n** jika tidak perlu banyak recommendations:
   ```bash
   python evaluate_system.py --top-n 5
   ```
