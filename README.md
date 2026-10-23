# autoedit

Membuat video otomatis dari **narasi audio**, **media berurutan**, dan **transcript**.

Setiap kalimat transcript dipetakan ke satu potongan visual, lalu semuanya dirender
menjadi MP4 dengan caption yang bisa ditempel permanen.

```
audio narasi + gambar 001.jpg, 002.jpg, ... + transcript
                          ↓
        Nama Project.mp4  +  Nama Project.timeline.json
```

## Fitur

- Antarmuka desktop **PySide6** dengan sidebar pengaturan, tabel media, dan pratinjau gambar.
- Dua sumber timestamp: **Whisper** (audio ditranskripsi otomatis) atau **file SRT**
  (timestamp asli dipakai langsung).
- Transcript tunggal berupa `.txt` atau `.srt`, tanpa mode tambahan.
- Urutan media mengikuti nomor pada nama file (`001.jpg`, `002.jpg`, …).
- Peringatan nomor hilang, nomor ganda, dan file tanpa nomor.
- Caption otomatis dari setiap kalimat, dapat ditempel ke video.
- Gerakan halus zoom dan pan pada gambar agar tidak terasa statis.
- Manifest timeline JSON sebagai sumber kebenaran untuk render ulang.
- Progres pemrosesan ditampilkan langsung di jendela aplikasi.
- Semua proses berjalan lokal; tidak ada unggahan ke internet.

## Kebutuhan

- Windows 10 atau 11
- Python 3.10 atau lebih baru
- FFmpeg, dipilih dengan urutan berikut:
  1. variabel lingkungan `AUTOEDIT_FFMPEG`
  2. `ffmpeg` di `PATH`
  3. paket `imageio-ffmpeg` (terpasang otomatis sebagai dependensi)

Whisper hanya dibutuhkan bila transcript berupa `.txt`. Pemakaian pertama mengunduh
model ke folder `data/cache/whisper`.

## Pemasangan

```powershell
git clone https://github.com/<nama-anda>/autoedit.git
cd autoedit
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Menjalankan aplikasi

```powershell
autoedit
```

atau

```powershell
python -m autoedit
```

## Cara pakai

1. Pilih **audio narasi**.
2. Pilih **folder media** yang berisi gambar atau video bernomor.
3. Pilih **transcript** berupa `.txt` atau `.srt`.
4. Tentukan **sumber timestamp**: otomatis, Whisper, atau SRT.
5. Atur nama project, resolusi, FPS, dan folder output.
6. Klik **Buat video**.

Sumber timestamp **otomatis** memilih SRT bila transcript berekstensi `.srt`,
dan Whisper bila berekstensi `.txt`.

Hasil yang dibuat di folder output:

```text
output/
├── Nama Project.mp4
└── Nama Project.timeline.json
```

## Format input

### Media

```text
001.jpg
002.jpg
003.mp4
```

Ekstensi gambar: `.jpg .jpeg .png .webp .bmp .gif .tif .tiff`
Ekstensi video: `.mp4 .mov .mkv .avi .webm .m4v .wmv`

Jumlah media harus sama dengan jumlah kalimat pada transcript. Bila jumlahnya berbeda,
aplikasi menampilkan pesan seperti
`Transcript memiliki 6 kalimat tetapi media berisi 5 file`.

### Transcript `.txt`

```text
Pernahkah kamu membayangkan apa yang terjadi?
Dunia perlahan akan berubah menjadi gelap.
```

Kalimat dipisah berdasarkan tanda baca `. ! ? … 。！？`, bukan berdasarkan baris baru.
File `.txt` memerlukan Whisper untuk menentukan timestamp.

### Transcript `.srt`

```srt
1
00:00:00,590 --> 00:00:04,050
Pernahkah kamu membayangkan apa yang terjadi?

2
00:00:04,050 --> 00:00:09,210
Dunia perlahan akan berubah menjadi gelap.
```

Setiap cue mewakili satu kalimat. Jeda antar cue dirapatkan otomatis, tumpang tindih
dipotong, dan cue yang melewati durasi audio dipangkas.

## Struktur project

```text
src/autoedit/
├── core/      manifest, probe, scanner, numbering, planner
├── speech/    splitter, tokenizer, srt_parser, aligner, normalizer, whisper
├── render/    ffmpeg, filters, captions, renderer
├── app/       pipeline, settings
├── gui/       jendela PySide6, tema, widget
├── assets/    logo aplikasi dan ikon kecil untuk tema antarmuka
└── runtime.py penyimpanan sementara, cache, dan pencarian aset
```

## Pengujian

```powershell
py -m pytest
```

## Membuat file `.exe`

Build memakai [PyInstaller](https://pyinstaller.org) dalam mode *onedir*, sehingga hasilnya
adalah folder `dist\autoedit\` berisi `autoedit.exe` beserta dependensinya.

```powershell
py -m pip install pyinstaller
.\build.ps1
```

Konfigurasi build ada di `autoedit.spec`: ikon aplikasi, aset tema, FFmpeg, dan model
Whisper ikut dibundel, sementara komponen Qt yang tidak dipakai dibuang. Ukuran folder
hasil sekitar **386 MB**, sebagian besar berasal dari FFmpeg, PyAV, CTranslate2, dan
ONNX Runtime yang dibutuhkan fitur Whisper.

Folder `build/` dan `dist/` tidak ikut masuk repositori. Pada versi `.exe`, data
(cache model, berkas sementara, preferensi) disimpan di `data\` yang sejajar dengan
`autoedit.exe`, sehingga folder hasil build bisa dipindah atau disalin utuh.

## Penyimpanan data

Aplikasi menyimpan cache Whisper, berkas sementara, dan preferensi di folder `data/`.
Folder ini tidak ikut masuk repositori. Lokasinya dapat dipindahkan dengan variabel
lingkungan `AUTOEDIT_DATA_DIR`.

## Lisensi

Dirilis di bawah [MIT License](LICENSE).
