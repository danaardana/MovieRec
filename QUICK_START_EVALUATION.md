# Quick Start: Evaluasi Performa

## Penggunaan Cepat

**⚠️ PENTING: Untuk dataset besar, selalu gunakan `--max-users` dan `--max-movies`!**

**⚠️ FAST MODE adalah default dan direkomendasikan!** Evaluasi sekarang jauh lebih cepat karena hanya memprediksi rating untuk test movies, bukan semua unrated movies.

### Evaluasi dengan Dataset Terbatas (DISARANKAN)

```bash
# Evaluasi cepat dengan dataset terbatas
python evaluate_system.py --max-users 2000 --max-movies 2000 --sample-users 100
```

**JANGAN** menjalankan tanpa `--max-users` dan `--max-movies` pada dataset besar, karena akan sangat lambat atau stuck!

## Contoh Penggunaan

### Evaluasi Dasar (Fast Mode - Recommended)
```bash
# SELALU gunakan max-users dan max-movies untuk dataset besar!
python evaluate_system.py --max-users 2000 --max-movies 2000
```

### Evaluasi pada 50 Pengguna (Lebih Cepat)
```bash
python evaluate_system.py --sample-users 50
```

### Evaluasi dengan Top-20 Rekomendasi
```bash
python evaluate_system.py --top-n 20 --sample-users 100
```

### Evaluasi Super Cepat (Skip Diversity Calculation)
```bash
python evaluate_system.py --sample-users 100 --skip-diversity
```

### Evaluasi dengan Output di Direktori Kustom
```bash
python evaluate_system.py --output-dir my_evaluation_results
```

### Standard Mode (Lebih Lambat, Prediksi Semua Movies)
Jika Anda ingin evaluasi yang lebih akurat (memprediksi semua unrated movies):

```bash
python evaluate_system.py --standard-mode
```

**Catatan**: Standard mode jauh lebih lambat karena memprediksi rating untuk semua unrated movies. Gunakan hanya jika diperlukan untuk akurasi maksimal.

## Output yang Dihasilkan

Setelah evaluasi selesai, hasil akan disimpan di direktori `evaluation_results/` (atau direktori yang Anda tentukan) dengan 4 format:

1. **`evaluation_YYYYMMDD_HHMMSS.json`** - Data terstruktur (untuk program)
2. **`evaluation_YYYYMMDD_HHMMSS.csv`** - Tabel metrik (untuk Excel/Spreadsheet)
3. **`evaluation_YYYYMMDD_HHMMSS.log`** - Log terstruktur dengan timestamp
4. **`evaluation_YYYYMMDD_HHMMSS.txt`** - Teks mudah dibaca (untuk manusia)

## Metrik yang Diukur

- **MAE & RMSE**: Akurasi prediksi rating
- **Precision, Recall, F1**: Kualitas ranking rekomendasi
- **NDCG**: Kualitas ranking dengan mempertimbangkan posisi
- **Diversity**: Keragaman rekomendasi (berdasarkan genre)
- **Coverage**: Persentase item yang dapat direkomendasikan
- **Cold Start Rate**: Persentase pengguna yang menggunakan fallback

Lihat `README_EVALUATION.md` untuk dokumentasi lengkap.
