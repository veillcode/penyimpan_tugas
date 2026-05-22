"""
back.py — Backend Flask untuk Aplikasi Penyimpanan Tugas & Dokumen
Jalankan dengan: python back.py
Server berjalan di: http://127.0.0.1:5000
"""

import os
import sqlite3
import hashlib
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ── Konfigurasi ─────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "database.db")
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXT = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
               "txt", "png", "jpg", "jpeg", "gif", "zip"}

if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

app = Flask(__name__)
CORS(app)   # Izinkan request dari file HTML yang dibuka di browser

# ── Helper ───────────────────────────────────────────────────────────────────
def get_db():
    """Buka koneksi SQLite (buat database jika belum ada)."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def init_db():
    """Buat tabel users dan tasks jika belum ada."""
    with get_db() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    UNIQUE NOT NULL,
                password TEXT    NOT NULL,
                created  TEXT    DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                title      TEXT    NOT NULL,
                file_name  TEXT,
                file_path  TEXT,
                completed  INTEGER DEFAULT 0,
                created    TEXT    DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

# ── Endpoint: Register ────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(status="error", pesan="Username dan Password tidak boleh kosong."), 400

    try:
        with get_db() as con:
            con.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_password(password))
            )
        return jsonify(status="sukses", pesan="Akun berhasil dibuat!"), 201
    except sqlite3.IntegrityError:
        return jsonify(status="error", pesan="Username sudah terdaftar!"), 409

# ── Endpoint: Login ───────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(status="error", pesan="Username dan Password tidak boleh kosong."), 400

    with get_db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    if not user:
        return jsonify(status="error", pesan="Akun belum terdaftar!"), 404
    if user["password"] != hash_password(password):
        return jsonify(status="error", pesan="Username atau Password salah!"), 401

    return jsonify(status="sukses", pesan="Login berhasil!", user_id=user["id"], username=user["username"])

# ── Endpoint: Upload Tugas ────────────────────────────────────────────────────
@app.route("/upload-tugas", methods=["POST"])
def upload_tugas():
    user_id   = request.form.get("user_id")
    nama_tugas = request.form.get("nama_tugas", "").strip()
    file_obj  = request.files.get("dokumen")

    if not user_id or not nama_tugas:
        return jsonify(status="error", pesan="user_id dan nama_tugas wajib diisi."), 400

    file_name = None
    file_link = None

    if file_obj and file_obj.filename:
        if not allowed_file(file_obj.filename):
            return jsonify(status="error", pesan="Tipe file tidak diizinkan."), 400

        ext       = file_obj.filename.rsplit(".", 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        file_obj.save(file_path)

        file_name = file_obj.filename          # Nama asli untuk ditampilkan
        file_link = f"http://127.0.0.1:5000/uploads/{safe_name}"

    with get_db() as con:
        cur = con.execute(
            "INSERT INTO tasks (user_id, title, file_name, file_path) VALUES (?, ?, ?, ?)",
            (user_id, nama_tugas, file_name, safe_name if file_name else None)
        )
        task_id = cur.lastrowid

    return jsonify(
        status    = "sukses",
        task_id   = task_id,
        nama_tugas = nama_tugas,
        nama_file  = file_name,
        link_file  = file_link
    ), 201

# ── Endpoint: Ambil Semua Tugas User ─────────────────────────────────────────
@app.route("/tugas/<int:user_id>", methods=["GET"])
def get_tugas(user_id):
    with get_db() as con:
        rows = con.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC", (user_id,)
        ).fetchall()

    tasks = []
    for r in rows:
        tasks.append({
            "id"        : r["id"],
            "title"     : r["title"],
            "file"      : r["file_name"],
            "link"      : f"http://127.0.0.1:5000/uploads/{r['file_path']}" if r["file_path"] else None,
            "completed" : bool(r["completed"]),
            "created"   : r["created"]
        })

    return jsonify(status="sukses", tasks=tasks)

# ── Endpoint: Toggle Selesai/Belum ───────────────────────────────────────────
@app.route("/tugas/<int:task_id>/toggle", methods=["PATCH"])
def toggle_tugas(task_id):
    with get_db() as con:
        task = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return jsonify(status="error", pesan="Tugas tidak ditemukan."), 404
        new_status = 0 if task["completed"] else 1
        con.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_status, task_id))

    return jsonify(status="sukses", completed=bool(new_status))

# ── Endpoint: Hapus Tugas ─────────────────────────────────────────────────────
@app.route("/tugas/<int:task_id>", methods=["DELETE"])
def delete_tugas(task_id):
    with get_db() as con:
        task = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return jsonify(status="error", pesan="Tugas tidak ditemukan."), 404

        # Hapus file fisik jika ada
        if task["file_path"]:
            fp = os.path.join(UPLOAD_DIR, task["file_path"])
            if os.path.exists(fp):
                os.remove(fp)

        con.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    return jsonify(status="sukses", pesan="Tugas berhasil dihapus.")

# ── Endpoint: Serve File Upload ───────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ── Jalankan Server ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  Server berjalan di http://127.0.0.1:5000")
    print("  Tekan CTRL+C untuk menghentikan")
    print("=" * 50)
    app.run(debug=True, port=5000)
