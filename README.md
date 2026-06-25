# Bot Telegram Timesheet & Pengingat Harian (Lightweight)

Bot Telegram ini adalah asisten pribadi (Single User) untuk mencatat aktivitas kerja harian (Timesheet) dan memberikan pengingat harian agar Anda tidak lupa mengisi timesheet. 

Bot ini dirancang agar **sangat ringan**, berjalan asinkron menggunakan Python, SQLite sebagai database lokal, dan dikelola menggunakan **UV (Astral)** sebagai package manager.

## 🚀 Fitur Utama
- **Pencatatan Cepat**: Cukup ketik `/isi [Project], [Durasi], [Deskripsi]` (misal: `/isi Project A, 3.5, Coding REST API`).
- **Laporan Otomatis**: Generate laporan interaktif lewat tombol menu untuk rentang waktu Hari Ini, Kemarin, Minggu Ini, atau Bulan Ini.
- **Ekspor CSV**: Menghasilkan ringkasan teks di chat sekaligus mengirimkan file `.csv` yang bisa diunduh dan dibuka di Excel/Spreadsheet.
- **Laporan Kustom**: Mendukung pencarian tanggal manual, contoh: `/laporan 25-06-2026` atau `/laporan 01-06-2026 s/d 15-06-2026`.
- **Pengingat Harian**: Mengirimkan pengingat otomatis setiap hari kerja (Senin - Jumat) di jam yang bisa ditentukan sendiri.
- **Aman (Single User)**: Hanya merespon pesan dari Telegram User ID Anda yang dikonfigurasikan di file `.env`.

---

## 🛠️ Instalasi & Persiapan

### 1. Prasyarat
Pastikan Anda sudah menginstal Python dan **uv** (Astral). Jika belum menginstal `uv`, Anda bisa menginstalnya dengan perintah berikut:
- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS/Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 2. Kloning / Unduh Proyek
Arahkan terminal ke folder proyek ini.

### 3. Konfigurasi Bot (.env)
1. Salin berkas `.env.example` menjadi `.env`
2. Buka `.env` dan lengkapi konfigurasi berikut:
   - `TELEGRAM_BOT_TOKEN`: Dapatkan dari [@BotFather](https://t.me/BotFather) saat membuat bot baru.
   - `AUTHORIZED_USER_ID`: ID akun Telegram Anda. Anda dapat mengetahui ID Anda dengan mengirimkan pesan ke [@userinfobot](https://t.me/userinfobot).

---

## 🏃 Menyinkronkan dan Menjalankan Bot

Gunakan `uv` untuk menginstal dependensi secara otomatis ke virtual environment (`.venv`) dan menjalankan bot:

```bash
uv run bot.py
```

`uv run` akan mendeteksi dependensi dari `pyproject.toml`, membuat virtual environment jika belum ada, lalu menjalankan script bot dengan aman dan cepat.

---

## 📝 Panduan Perintah Bot (Telegram Commands)

- `/start` - Menampilkan ucapan selamat datang dan menu awal.
- `/help` - Menampilkan panduan lengkap penggunaan perintah bot.
- `/status` - Menampilkan status aktif pengingat dan jam pengingat saat ini.
- `/isi [Project], [Durasi], [Deskripsi]` - Mencatat entri timesheet baru untuk tanggal hari ini.
- `/laporan` - Menampilkan tombol interaktif untuk memilih laporan periode instan.
- `/laporan [tanggal]` - Meminta laporan tanggal manual.
  - _Contoh Tanggal Tunggal:_ `/laporan 25-06-2026`
  - _Contoh Rentang Tanggal:_ `/laporan 01-06-2026 s/d 15-06-2026`
- `/set_pengingat [HH:MM]` - Mengatur jam pengingat harian (format 24 jam). Contoh: `/set_pengingat 17:30`
- `/pengingat_on` - Mengaktifkan kembali pengingat harian (Senin - Jumat).
- `/pengingat_off` - Mematikan pengingat harian.

---

## 📂 Struktur Database (`timesheet.db`)

Bot ini menggunakan SQLite yang disimpan secara lokal dalam satu berkas `timesheet.db`.
1. **`timesheets`**: Menyimpan kolom `id`, `project`, `duration` (dalam jam), `description`, `date` (format `YYYY-MM-DD`), dan `created_at`.
2. **`settings`**: Menyimpan konfigurasi per user (User ID, Waktu Pengingat, Status Aktif).

---

## 🖥️ Menjalankan Bot di Background (Linux Server)

Agar bot Anda terus berjalan 24/7 di server Linux, Anda dapat menggunakan salah satu metode berikut:

### Opsi 1: Menggunakan Systemd Service (Sangat Direkomendasikan)
Ini adalah metode standar produksi pada Linux untuk menjalankan bot sebagai *system service*.

1. Buat file service baru di direktori systemd:
   ```bash
   sudo nano /etc/systemd/system/timesheet-bot.service
   ```

2. Tempelkan konfigurasi berikut (sesuaikan `User` dan `WorkingDirectory` dengan username dan path proyek Anda):
   ```ini
   [Unit]
   Description=Telegram Timesheet Bot Service
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/Timesheet
   # Menjalankan langsung menggunakan interpreter python dari virtual environment yang dibuat uv
   ExecStart=/home/ubuntu/Timesheet/.venv/bin/python bot.py
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Simpan file tersebut, lalu jalankan perintah berikut untuk memuat ulang dan mengaktifkan service:
   ```bash
   # Reload systemd manager configuration
   sudo systemctl daemon-reload

   # Aktifkan agar otomatis berjalan saat server booting
   sudo systemctl enable timesheet-bot

   # Jalankan service bot
   sudo systemctl start timesheet-bot
   ```

4. Perintah untuk mengelola service:
   - Cek status: `sudo systemctl status timesheet-bot`
   - Hentikan bot: `sudo systemctl stop timesheet-bot`
   - Restart bot: `sudo systemctl restart timesheet-bot`
   - Lihat log bot: `journalctl -u timesheet-bot -f`

---

### Opsi 2: Menggunakan Nohup (Sederhana tanpa instalasi apa pun)
Jika Anda hanya ingin menjalankan bot dengan cepat tanpa konfigurasi tambahan.

1. Jalankan bot di background:
   ```bash
   nohup uv run bot.py > bot.log 2>&1 &
   ```
2. File log akan ditulis ke `bot.log`. Untuk menghentikan bot, cari PID-nya lalu kill:
   ```bash
   pkill -f "python bot.py"
   ```

