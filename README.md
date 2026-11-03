# adp-ad-config

Config iklan remote (GitHub Pages). Satu file per app: `v1/<package>.json`.

## File

- `v1/<package>.json` - config iklan satu app (dibaca app lewat URL Pages)
- `schema/ad-config.schema.json` - aturan JSON Schema; juga sumber regex unitId
- `.vscode/settings.json` - hubungkan schema ke `v1/*.json` (typo langsung digaris merah, hover = penjelasan)
- `scripts/validate.py` - validator (python3, tanpa dependensi)
- `.githooks/pre-commit` - jalankan validator, commit diblokir kalau ada error
- `scripts/new-app.sh` - buat config app baru dari unit ID test

## Alur harian

1. Edit `v1/<package>.json` di VS Code (error muncul saat mengetik).
2. `git add` + `git commit` (hook validasi otomatis).
3. `git push`. Tunggu propagasi 40-90 detik.

Cek manual: `python3 scripts/validate.py`

Setup sekali per clone: `git config core.hooksPath .githooks`

## App baru

```sh
./scripts/new-app.sh <package> [everyNTaps=10] [cooldownSec=30]
```

Membuat file dengan 4 unit ID test Google, semua enabled. Ganti unit ID asli lalu commit.

## Tambah publisher baru

Dua tempat harus diubah:

1. Schema: `definitions.unitId.pattern` di `schema/ad-config.schema.json` (tambah ID publisher di grup `(a|b|c)`). Validator ikut otomatis.
2. App: konstanta `ALLOWED_PUBLISHERS` di kode app.

## Cek live

```sh
curl -s https://salsabilaemma.github.io/ADP-Ad-Config
```

Propagasi setelah push: 40-90 detik.
