# Troubleshooting - Evaluasi Lambat

## Masalah: Evaluasi Stuck atau Sangat Lambat

Jika evaluasi stuck atau sangat lambat, kemungkinan besar Anda menggunakan dataset yang **sangat besar** tanpa membatasi ukurannya.

### Gejala
- Evaluasi stuck di "Splitting data into train/test sets..."
- Dataset besar (> 100K users, > 10M ratings)
- Tidak ada progress update

### Penyebab
Dataset MovieLens bisa sangat besar (30M+ ratings, 300K+ users). Memproses semua data memakan waktu sangat lama bahkan dengan optimasi.

### Solusi: Gunakan --max-users dan --max-movies

**Selalu gunakan `--max-users` dan `--max-movies` untuk membatasi ukuran dataset!**

```bash
# ✅ BAIK - Evaluasi cepat dengan dataset terbatas
python evaluate_system.py --max-users 2000 --max-movies 2000 --sample-users 100

# ❌ BURUK - Akan sangat lambat atau stuck
python evaluate_system.py --sample-users 100
```

### Contoh Penggunaan yang Disarankan

#### Untuk Evaluasi Cepat (Testing)
```bash
python evaluate_system.py \
    --max-users 1000 \
    --max-movies 1000 \
    --sample-users 50 \
    --top-n 10 \
    --skip-diversity
```

#### Untuk Evaluasi Sedang
```bash
python evaluate_system.py \
    --max-users 2000 \
    --max-movies 2000 \
    --sample-users 100 \
    --top-n 10
```

#### Untuk Evaluasi Lengkap (Tetap Terbatas)
```bash
python evaluate_system.py \
    --max-users 5000 \
    --max-movies 5000 \
    --sample-users 500 \
    --top-n 10
```

### Perkiraan Waktu

| Max Users | Max Movies | Sample Users | Perkiraan Waktu |
|-----------|------------|--------------|-----------------|
| 1000 | 1000 | 50 | ~1-2 menit |
| 2000 | 2000 | 100 | ~3-5 menit |
| 5000 | 5000 | 500 | ~10-20 menit |
| **Tidak dibatasi** | **Tidak dibatasi** | 100 | **~jam atau stuck!** |

### Tips Tambahan

1. **Mulai kecil**: Mulai dengan dataset kecil (1000 users/movies) untuk memastikan semuanya bekerja
2. **Tingkatkan bertahap**: Setelah berhasil, tingkatkan ukuran dataset sesuai kebutuhan
3. **Gunakan --skip-diversity**: Untuk evaluasi lebih cepat, gunakan `--skip-diversity`
4. **Monitor progress**: Progress akan ditampilkan setiap 10K users untuk dataset besar

### Jika Masih Lambat

Jika masih lambat bahkan dengan max-users/max-movies:

1. Kurangi lebih lanjut: `--max-users 500 --max-movies 500`
2. Kurangi sample users: `--sample-users 20`
3. Gunakan skip diversity: `--skip-diversity`
4. Gunakan top-n lebih kecil: `--top-n 5`

### Catatan

Dataset yang lebih kecil (1000-5000 users/movies) biasanya sudah cukup untuk mendapatkan metrik evaluasi yang representatif dan akurat. Anda tidak perlu memproses semua 300K users untuk mendapatkan hasil yang baik!
