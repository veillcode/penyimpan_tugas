# Penyimpanan Tugas & Dokumen

## Struktur File
```
project/
├── back.py        ← Backend Flask (server)
├── index.html     ← Frontend (buka di browser)
├── database.db    ← Dibuat otomatis saat pertama jalan
└── uploads/       ← Folder file upload (dibuat otomatis)
```

## Cara Menjalankan

### 1. Install Dependensi Python
```bash
pip install flask flask-cors
```

### 2. Jalankan Backend
```bash
python back.py
```
Server akan berjalan di **http://127.0.0.1:5000**

### 3. Buka Frontend
Buka file `index.html` langsung di browser (double-click), atau:
```bash
# Jika punya Python:
python -m http.server 8080
# Lalu buka http://localhost:8080/index.html
```

## Fitur
- **Register & Login** — data disimpan di SQLite dengan password ter-hash (SHA-256)
- **Upload Tugas + Dokumen** — file disimpan di folder `uploads/`
- **Buka File** — klik nama file untuk membuka/download dokumen
- **Tandai Selesai** — toggle status tugas hijau/abu-abu
- **Hapus Tugas** — file fisik ikut terhapus dari server

## API Endpoints
| Method | URL | Fungsi |
|--------|-----|--------|
| POST | `/register` | Daftar akun baru |
| POST | `/login` | Masuk ke akun |
| POST | `/upload-tugas` | Simpan tugas + upload file |
| GET  | `/tugas/<user_id>` | Ambil semua tugas user |
| PATCH | `/tugas/<id>/toggle` | Toggle status selesai |
| DELETE | `/tugas/<id>` | Hapus tugas & file |
