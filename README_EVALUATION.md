# Evaluasi Performa Sistem Rekomendasi

Modul evaluasi ini menyediakan evaluasi performa numerik yang komprehensif untuk sistem rekomendasi MovieRec menggunakan berbagai metrik kuantitatif.

## 📋 Fitur

### Metrik yang Diukur

1. **Rating Prediction Metrics** (untuk prediksi rating eksplisit):
   - **MAE** (Mean Absolute Error): Rata-rata selisih absolut antara prediksi dan rating aktual
   - **RMSE** (Root Mean Squared Error): Akar dari rata-rata kuadrat selisih

2. **Ranking Metrics** (untuk rekomendasi top-N):
   - **Precision@K**: Proporsi item yang direkomendasikan yang relevan
   - **Recall@K**: Proporsi item relevan yang direkomendasikan
   - **F1@K**: Rata-rata harmonik dari precision dan recall
   - **NDCG@K** (Normalized Discounted Cumulative Gain): Mengukur kualitas ranking

3. **Diversity Metrics**:
   - **Intra-list Diversity**: Keragaman dalam daftar rekomendasi (berdasarkan genre)
   - **Genre Coverage**: Cakupan genre yang direkomendasikan
   - **Unique Genres**: Jumlah genre unik dalam rekomendasi

4. **Metrik Tambahan**:
   - **Coverage**: Persentase item dalam katalog yang dapat diprediksi
   - **Cold Start Rate**: Persentase pengguna yang menggunakan fallback popular movies

### Format Output

Evaluasi menghasilkan hasil dalam **4 format berbeda**:

1. **JSON** (`.json`): Format terstruktur untuk pemrosesan programatik
2. **CSV** (`.csv`): Tabel metrik yang mudah dibaca di spreadsheet
3. **Log** (`.log`): File log terstruktur dengan timestamp
4. **Text** (`.txt`): File teks yang mudah dibaca manusia

## 🚀 Penggunaan

### Quick Start

Evaluasi dengan pengaturan default:

```bash
python evaluate_system.py
```

### Opsi Lanjutan

```bash
python evaluate_system.py \
    --sample-users 100 \
    --top-n 10 \
    --test-ratio 0.2 \
    --output-dir evaluation_results \
    --rating-threshold 3.5
```

### Parameter yang Tersedia

| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| `--ratings-path` | `dataset/ratings.csv` | Path ke file ratings.csv |
| `--movies-path` | `dataset/movies.csv` | Path ke file movies.csv |
| `--test-ratio` | `0.2` | Rasio data untuk testing (0.0-1.0) |
| `--sample-users` | `None` (semua) | Jumlah pengguna yang dievaluasi |
| `--top-n` | `10` | Jumlah rekomendasi per pengguna |
| `--min-ratings-per-user` | `5` | Minimum rating per pengguna untuk evaluasi |
| `--min-common-movies` | `5` | Minimum film bersama untuk perhitungan similarity |
| `--top-k-similar` | `50` | Jumlah pengguna serupa yang dipertimbangkan |
| `--rating-threshold` | `3.5` | Threshold rating untuk relevansi (>= threshold = relevan) |
| `--max-users` | `None` (semua) | Maksimum pengguna yang dimuat |
| `--max-movies` | `None` (semua) | Maksimum film yang dimuat |
| `--output-dir` | `evaluation_results` | Direktori untuk menyimpan hasil |
| `--random-seed` | `42` | Seed random untuk reproduksibilitas |

## 📊 Contoh Output

### File JSON

```json
{
  "evaluation_config": {
    "test_ratio": 0.2,
    "sample_users": 100,
    "top_n": 10,
    "rating_threshold": 3.5
  },
  "dataset_info": {
    "train_ratings_count": 16000,
    "test_ratings_count": 4000,
    "total_users": 100,
    "evaluated_users": 95
  },
  "rating_metrics": {
    "mae": 0.7234,
    "rmse": 0.9123,
    "count": 850
  },
  "ranking_metrics": {
    "precision@10": 0.3456,
    "recall@10": 0.2345,
    "f1@10": 0.2801,
    "ndcg@10": 0.4123
  },
  "diversity_metrics": {
    "avg_intra_list_diversity": 0.7234,
    "avg_genre_coverage": 0.4567,
    "avg_unique_genres": 4.5
  },
  "coverage": 0.6789,
  "cold_start_rate": 0.05,
  "timestamp": "2024-01-15T10:30:00"
}
```

### File CSV

```csv
category,metric,value
rating_metrics,mae,0.7234
rating_metrics,rmse,0.9123
rating_metrics,count,850
ranking_metrics,precision@10,0.3456
ranking_metrics,recall@10,0.2345
...
```

### File Log/TXT

```
================================================================================
MOVIE RECOMMENDATION SYSTEM EVALUATION RESULTS
================================================================================

EVALUATION CONFIGURATION:
  test_ratio: 0.2
  sample_users: 100
  top_n: 10
  ...

RATING PREDICTION METRICS:
  mae: 0.7234
  rmse: 0.9123
  count: 850

RANKING METRICS:
  precision@10: 0.3456
  recall@10: 0.2345
  f1@10: 0.2801
  ndcg@10: 0.4123
...
```

## 🔬 Metodologi Evaluasi

### Train-Test Split

- Data dibagi dengan rasio yang dapat dikonfigurasi (default: 80% train, 20% test)
- Split dilakukan per pengguna: untuk setiap pengguna, beberapa rating dipilih secara acak untuk testing
- Ini memastikan tidak ada data leakage

### Evaluasi Rating Prediction

- Untuk setiap pengguna dalam test set:
  - Sistem dilatih pada train data
  - Prediksi dibuat untuk item-item dalam test set
  - MAE dan RMSE dihitung dari prediksi vs rating aktual

### Evaluasi Ranking

- Item relevan didefinisikan sebagai item dengan rating >= threshold (default: 3.5)
- Precision, Recall, F1, dan NDCG dihitung untuk top-N rekomendasi
- Metrik diagregasi dengan rata-rata di semua pengguna

### Evaluasi Diversity

- Diversity dihitung menggunakan Jaccard distance antar genre
- Intra-list diversity: rata-rata jarak Jaccard antar pasangan item dalam daftar rekomendasi
- Genre coverage: jumlah genre unik yang direkomendasikan

## 📁 Struktur File

```
backend/
├── evaluator/
│   ├── __init__.py
│   ├── metrics.py          # Perhitungan metrik individual
│   └── evaluator.py        # Kelas evaluator utama

evaluate_system.py          # Script untuk menjalankan evaluasi
evaluation_results/         # Direktori output (dibuat otomatis)
├── evaluation_YYYYMMDD_HHMMSS.json
├── evaluation_YYYYMMDD_HHMMSS.csv
├── evaluation_YYYYMMDD_HHMMSS.log
└── evaluation_YYYYMMDD_HHMMSS.txt
```

## 💡 Tips Penggunaan

1. **Untuk evaluasi cepat**: Gunakan `--sample-users 50` untuk menguji pada subset kecil
2. **Untuk evaluasi lengkap**: Hapus `--sample-users` untuk mengevaluasi semua pengguna (mungkin lebih lambat)
3. **Tuning threshold**: Sesuaikan `--rating-threshold` berdasarkan interpretasi "relevan" untuk use case Anda
4. **Reproduksibilitas**: Gunakan `--random-seed` yang sama untuk mendapatkan hasil yang sama
5. **Eksperimen**: Simpan hasil dengan direktori berbeda menggunakan `--output-dir` untuk membandingkan konfigurasi

## 🔍 Interpretasi Metrik

### MAE dan RMSE
- **Lebih rendah = lebih baik**
- MAE: Rata-rata error absolut (lebih mudah diinterpretasi)
- RMSE: Lebih sensitif terhadap error besar (menghukum outlier lebih keras)

### Precision dan Recall
- **Precision**: Dari yang direkomendasikan, berapa banyak yang relevan?
- **Recall**: Dari yang relevan, berapa banyak yang direkomendasikan?
- **Trade-off**: Biasanya, meningkatkan precision menurunkan recall, dan sebaliknya

### NDCG
- **Lebih tinggi = lebih baik** (0-1)
- Mempertimbangkan posisi item relevan dalam ranking
- Item relevan di posisi teratas memberikan skor lebih tinggi

### Diversity
- **Lebih tinggi = lebih beragam**
- Penting untuk menghindari "filter bubble" - hanya merekomendasikan item serupa
- Trade-off dengan accuracy: lebih beragam mungkin sedikit menurunkan accuracy

### Coverage
- **Lebih tinggi = lebih baik** (0-1)
- Mengukur berapa banyak item dalam katalog yang dapat direkomendasikan
- Coverage rendah berarti sistem hanya merekomendasikan subset kecil dari katalog

## 📚 Referensi

- **MAE/RMSE**: Metrik standar untuk prediksi rating
- **Precision/Recall/F1**: Metrik standar dalam information retrieval
- **NDCG**: Metrik ranking yang umum digunakan dalam recommendation systems
- **Diversity**: Penting untuk menghindari homogenitas dalam rekomendasi

## ⚠️ Catatan

- Evaluasi dapat memakan waktu yang lama untuk dataset besar
- Pastikan dataset tersedia di path yang benar
- Hasil dapat bervariasi tergantung pada split data (gunakan random seed untuk konsistensi)
