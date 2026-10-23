# autoedit

Membuat video otomatis dari **narasi audio**, **media berurutan**, dan **transcript**.
Setiap kalimat transcript menjadi satu potongan visual, lalu semuanya dirender menjadi MP4
dengan caption yang bisa ditempel permanen.

## Fitur

- Dua sumber timestamp: **Whisper** (audio ditranskripsi otomatis) atau **file SRT** (timestamp asli dipakai langsung).
- Transcript tunggal, tanpa pilihan mode selain sumber timestamp.
- Urutan media mengikuti nomor pada nama file (`001.jpg`, `002.jpg`, …).
- Peringatan nomor hilang, nomor ganda, dan file tanpa nomor.
- Caption otomatis dari setiap kalimat, dapat ditempel ke video.
- Gerakan halus zoom dan pan pada gambar agar tidak terasa statis.
- Manifest timeline JSON sebagai sumber kebenaran untuk render ulang.
- Semua proses berjalan lokal; tidak ada unggahan ke internet.

## Kebutuhan

- Windows 10 atau 11
- Python 3.10 atau lebih baru
- FFmpeg tersedia di `PATH`, atau lewat `AUTOEDIT_FFMPEG`, atau paket `imageio-ffmpeg`

Whisper hanya dibutuhkan bila transcript berupa `.txt`. Pemakaian pertama mengunduh model
ke folder `data/cache/whisper`.

## Pemasangan

```powershell
cd D:\autoedit
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

Jumlah media harus sama dengan jumlah kalimat pada transcript.

### Transcript `.txt`

```text
Pernahkah kamu membayangkan apa yang terjadi?
Dunia perlahan akan berubah menjadi gelap.
```

Kalimat dipisah berdasarkan tanda baca `. ! ? … 。！？`, bukan berdasarkan baris baru.

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
├── gui/       aplikasi desktop, tema, widget
└── runtime.py penyimpanan sementara dan cache
```

## Pengujian

```powershell
py -m pytest
```

## Batasan

- Satu kalimat transcript dipetakan ke tepat satu media, berdasarkan urutan.
- Tidak ada analisis isi gambar; kecocokan visual sepenuhnya ditentukan urutan media.
- Rendering memakai satu proses FFmpeg per clip, sehingga video berdurasi panjang memerlukan waktu sebanding.
