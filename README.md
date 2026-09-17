# 📸 picpress

> **Repo name:** `picpress`

**picpress** is a fast, modern desktop app that compresses JPEG, PNG, WebP, BMP, and TIFF images with maximum quality preservation. Smart mode auto-picks the best format. Drag & drop support, batch processing, live savings stats, and a sleek dark UI. Builds to a single `.exe` with one click.

---

## Logos

| Lens (recommended) | Compress Frame | Bolt |
|:---:|:---:|:---:|
| ![Logo Lens](assets/logo-lens.jpeg) | ![Logo Compress](assets/logo-compress.jpeg) | ![Logo Bolt](assets/logo-bolt.jpeg) |

> Pick your favourite and rename it to `icon.ico` (convert with an online tool), then uncomment the `icon=` line in `photo_compressor.spec`.

---

## Features

| Feature | Detail |
|---|---|
| **Smart mode** | Tests WebP, PNG, JPEG — picks the smallest output automatically |
| **WebP** | Saves as `.webp` — typically 30–60 % smaller than JPEG |
| **JPEG optimized** | Progressive + optimized Huffman tables, EXIF preserved |
| **PNG lossless** | Zlib level-9, zero data loss (ideal for screenshots/logos) |
| **Drag & Drop** | Drop files straight onto the app window |
| **Quality slider** | 60–99 (default 85 — near-invisible difference vs. original) |
| **Batch** | Compress hundreds of images at once |
| **Per-file stats** | Original → compressed size and % saved per file |
| **Custom output folder** | Save to source folder or choose a destination |
| **Same filename** | Output keeps the original name; auto-suffix only prevents overwrite |
| **Never upsizes** | If a file is already optimal it is copied as-is |
| **EXIF preserved** | Camera, GPS, and date metadata carried through |

---

## Building the EXE (Windows)

1. Install **Python 3.10+** → [python.org](https://python.org)
2. Double-click **`build.bat`** and wait ~1 minute
3. Your EXE appears in `dist\PhotoCompressor.exe`
4. Fully self-contained — no Python needed on the target machine

## Running from source

```bash
pip install Pillow tkinterdnd2
python photo_compressor.py
```

## Supported formats

JPEG · PNG · WebP · BMP · TIFF

## Tips

- **Smart mode at quality 85** is the best all-round choice for photos.
- **PNG lossless** is ideal for screenshots, logos, and graphics with transparency.
- **WebP** is best when optimizing for the web.
- Quality below **80** can introduce visible artefacts in detailed areas.

## License

MIT
