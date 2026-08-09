# ContentSuite — AGENTS.md

## Project overview
Desktop app for **Windows** (primary) and **Linux** — content prep for **Patreon**, **Pixiv**, **X**, and **Bluesky**.

Stack: Python 3.11+, PySide6 (GUI), ffmpeg (video), Pillow (images + PDF). Config: `%APPDATA%/ContentSuite` (Windows) or `~/.config/ContentSuite` (Linux/XDG). Launch: `run.bat` / `run.sh`.

UI languages: English (default), Russian, Japanese — see `core/i18n.py` and `core/i18n_catalog.py`.

## Architecture
- `main.py` — QApplication entry point, main window with QTabWidget
- `tabs/images_tab.py` — images: compress, metadata strip, PDF
- `tabs/pixiv_preview_tab.py` — Pixiv collage cover (up to 3 artworks)
- `tabs/video_tab.py` — video: watermark, convert, GIF, ugoira, compression level UI
- `tabs/pixiv_censor_tab.py` — Pixiv censor export (video + images, lasso zones)
- `tabs/art_checker_tab.py` — Art Checker: JSON vs output folder, watch, copy names
- `core/pixiv_preview.py` — collage layouts on white background
- `core/compress.py` — image compression, metadata stripping, optional original filenames
- `core/pdf_export.py` — multi-page PDF via Pillow
- `core/watermark.py` — shared watermark logic (position, opacity) for images + video
- `core/ffmpeg_wrapper.py` — codec probe, convert, GIF, ugoira export
- `core/audio_head_fix.py` — detects the start-of-clip audio burst in AI-generated video
- `core/video_compression.py` — CRF presets (x264 / VP9) for re-encode jobs
- `core/config_store.py` — persistent settings (folders, watermarks, quality)
- `core/i18n.py` — UI translation manager
- `ui/image_grid.py` — image tile grid with hover preview
- `ui/clip_grid.py` — video clip grid with hover preview (QMediaPlayer)
- `ui/censor_media_grid.py` — mixed video + image grid for Pixiv censor tab
- `ui/art_checker_grid.py` — art checker tile grid (OK/MISS, variants, filter/sort)
- `ui/tile_style.py` — shared selected/unselected tile colors for all preview grids
- `ui/file_picker.py` — reusable path picker row (JSON/folder fields)
- `core/art_checker.py` — scan JSON arts against folder, sort/filter helpers
- `core/art_checker_trash.py` — session trash (`app_data_dir()/tmp`), cleared on startup
- `ui/censor_editor_dialog.py` — lasso zone editor (video frame or still image)
- `core/censor.py` — mosaic zones (polygon lasso + legacy rect), video/image export
- `ui/language_selector.py` — language switcher in toolbar

## Development rules (important for agents)
1. Each tab is an independent module — test separately before moving on.
2. Do **not** rewrite working modules when adding features — extend via new functions/classes
   while keeping public signatures backward-compatible.
3. Shared logic (watermark, ffmpeg, config, i18n) lives in `core/` — do not duplicate between tabs.
4. All user settings (folders, watermarks, compression params, `ui_language`) are persistent via
   `core/config_store.py`, never hardcoded.
5. Before implementing a feature, check the implementation status section below.
6. User-facing strings go through `tr("key")` in `core/i18n_catalog.py` (EN/RU/JA).

## Versioning (do not forget)
- **Single source of truth:** `core/credits.py` → `APP_VERSION` (semver, e.g. `1.1.0`).
- Shown in **About** dialog (`ui/about_dialog.py`) via `tr("about.version", version=APP_VERSION)`.
- When bumping a release: update `APP_VERSION`, git tag `v{APP_VERSION}`, and `RELEASE.md` / GitHub Actions tag push.
- Do not hardcode version strings elsewhere.

## Implementation status (update after each milestone)
- [x] Stage 1: basic shell, QTabWidget, input/output folder pickers
- [x] Stage 2: image compression + metadata removal (images_tab)
- [x] Stage 3: PDF export via Pillow
- [x] Pixiv preview: collage cover up to 3 artworks on white background
- [ ] Stage 4: watermark picker for images (position/opacity UI)
- [x] Stage 5: video_tab — codec probe (ffprobe), video watermark
- [x] Stage 6: GIF export (fps / width)
- [x] Stage 7: mp4/webm/mov convert, metadata removal, audio on/off
- [x] Video compression: dropdown presets (maximum → minimal / near-lossless), `video_compression_level` in config
- [x] Stage 8: ugoira export (frames + animation.json), optional watermark
- [x] Stage 9: clip grid with hover preview + audio
- [x] Stage 10 (partial): persistent config for watermarks and video settings
- [x] Pixiv censor tab: lasso zone editor, video + images, export to pixiv/
- [x] i18n: EN / RU / JA with toolbar language selector
- [x] Image grid hover preview with active-window guard
- [x] Optional keep-original-filename on image export
- [x] Art Checker tab: JSON scan, OK/MISS grid, folder watch, variant wheel, filter/sort, Del → session trash
- [x] Unified tile selection styling across image, clip, censor, and art checker grids
- [x] Images tab: grid sort by name or date (newest)
- [x] Video tab: auto-fix for the audio click at clip start (`video_fix_audio_head`)

## Watermark details
- Position is in % of frame (0.0–1.0 on X/Y), not pixels — works at any resolution.
- Opacity: alpha 0–100, applied via ffmpeg `overlay` + `colorchannelmixer` or Pillow alpha paste.
- Watermark file list is stored as paths in config; UI uses dropdown + “Add…”.

## Art Checker
- JSON path + scan folder; `scan_arts` maps file stems (`name`, `name_2`, …) to JSON art names.
- Grid: OK/MISS badges, hover preview, wheel cycles duplicate renders, double-click copies JSON **name**.
- **Del** — `move_to_trash()` moves the hovered (or selected) variant out of the scan folder into `%APPDATA%/ContentSuite/tmp` (Linux: `~/.config/ContentSuite/tmp`). Folder is wiped on each app start (`reset_trash_on_startup` in `main.py`).
- Folder watch debounces rescans; filter/sort persisted as `art_checker_filter`, `art_checker_sort`.

## Pixiv censor
- Input folder: videos and images together (`collect_censor_media` — videos first, then images).
- Zones: lasso polygon (`CensorZone.polygon`); hold LMB in editor, contour auto-closes.
- Legacy rect zones in `censor_zones.json` still export correctly.
- Editor: `CensorEditorDialog` accepts multiple selected paths; ←/→ navigates, zones auto-save on switch.
- Video export: `apply_video_censor` — ffmpeg mask per zone, output `pixiv/name_N.mp4`.
- Image export: `apply_image_censor` — Pillow mosaic inside polygon, output `pixiv/name_N.jpg`.
- Block size (pixel mosaic) — `pixiv_censor_block_size` in config; default 18.

## Video compression
- Presets in `core/video_compression.py`: `maximum`, `high`, `medium`, `near_lossless`, `minimal`.
- UI dropdown on Video tab → Convert block; persisted as `video_compression_level` (default `medium`).
- Applied when ffmpeg re-encodes: WebM output always; MP4/MOV only with “Re-encode video” checked.
- Also used by watermark export (VP9 webm) and Pixiv censor export (reads same config key).
- “Near lossless” / “Minimal” — low CRF (18–14 x264, 22–16 VP9) for space savings with no visible loss.

## Audio head fix (AI clips)
- Video models with an audio branch (MiniMax H3, LTX-2) emit a short loud click in the first
  ~0.4 s — garbage in the leading audio latents, not something a prompt can remove.
- `core/audio_head_fix.py` decodes only the first 1.2 s (mono 16 kHz PCM via ffmpeg pipe) and
  looks for the signature: a peak within the first 150 ms that drops into a pause of ≥150 ms.
  Clips that genuinely open with sound keep a loud tail and are returned as clean.
- The fix is `afade=t=in:st=<burst end>:d=0.06` — the head is silenced, **nothing is cut**, so
  the timeline never shifts and lip sync survives. Never replace this with a trim.
- Applied in `apply_watermark` and `convert_video` via the `audio_head=` argument; detection
  runs once per file in `_process_one`. Skipped when audio is copied (`-c:a copy`) or dropped.
- UI: checkbox on the Video tab → Convert block, `video_fix_audio_head` in config, default off.
  Muted length is reported per file in the log via `VideoJobResult.audio_head_ms`.

## ffmpeg wrapper requirements
- Before convert: `ffprobe` for input codec/container; wrap all subprocess calls in try/except;
  never crash the GUI — log errors to the log panel.
- Ugoira: export frames + `.json` (frame delays), compatible with Pixiv upload format.
- Re-encode paths call `ffmpeg_video_encode_args(format, compression_level)` from `core/video_compression.py`.