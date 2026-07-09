"""UI string catalog: English (default), Russian, Japanese."""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "lang.label": "Language",
        "lang.en": "English",
        "lang.ru": "Русский",
        "lang.ja": "日本語",
        "menu.settings": "Settings",
        "menu.author_metadata": "Author & metadata…",
        "menu.open_log": "Open session log…",
        "tab.images": "Images",
        "tab.pixiv_preview": "Pixiv Preview",
        "tab.video": "Video",
        "tab.pixiv_censor": "Pixiv Censor",
        "tab.art_checker": "Art Checker",
        "common.browse": "Browse…",
        "common.content_suite": "ContentSuite",
        "common.add": "Add…",
        "common.remove": "Remove",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.ok": "OK",
        "menu.about": "About ContentSuite…",
        "about.title": "About ContentSuite",
        "about.version": "v{version}",
        "about.body": (
            "<p>Created by <a href='{author_url}'>{author}</a><br>"
            "<a href='{repo_url}'>GitHub repository</a></p>"
            "<p><b>{ai_label}</b><br>"
            "Co-development: {ai_coauthor} · {ai_tool}</p>"
        ),
        "common.dpi": "DPI",
        "common.fps": "FPS",
        "unit.sec": " s",
        "unit.mb": " MB",
        "unit.time_sec": "{value:.1f} s",
        "common.not_selected": "(not selected)",
        "folder.placeholder": "Choose a folder…",
        "folder.dialog": "Choose folder — {label}",
        "file.placeholder": "Choose a file…",
        "file.dialog": "Choose file — {label}",
        "file.filter_json": "JSON (*.json);;All (*.*)",
        "art_checker.json": "Prompt book (JSON):",
        "art_checker.scan_folder": "Scan folder:",
        "art_checker.refresh": "Refresh",
        "art_checker.auto_watch": "Watch folder for changes",
        "art_checker.auto_watch_tip": (
            "Re-scan automatically when files are added, removed, or renamed in the scan folder."
        ),
        "art_checker.filter": "Filter:",
        "art_checker.sort": "Sort:",
        "art_checker.sort_name": "Name",
        "art_checker.sort_date": "Date (newest)",
        "art_checker.sort_missing_first": "Missing first",
        "art_checker.search": "Search:",
        "art_checker.copy_name": "Copy selected name",
        "art_checker.copy_missing": "Copy all missing",
        "art_checker.extra_group": "Extra files (not in JSON)",
        "art_checker.arts_group": "Arts",
        "art_checker.col_index": "#",
        "art_checker.col_status": "Status",
        "art_checker.col_section": "Section",
        "art_checker.col_name": "Name",
        "art_checker.col_files": "Files found",
        "art_checker.filter_all": "All",
        "art_checker.filter_missing": "Missing",
        "art_checker.filter_present": "Present",
        "art_checker.filter_sfw": "sfw",
        "art_checker.filter_nsfw": "nsfw",
        "art_checker.filter_sex": "sex",
        "art_checker.status_present": "OK",
        "art_checker.status_missing": "MISS",
        "art_checker.summary_idle": "Choose a JSON file and scan folder, then press Refresh.",
        "art_checker.summary": (
            "JSON: {total} arts · unique files: {files} · "
            "present: {present} · missing: {missing} · extra: {extra}"
        ),
        "art_checker.extra_none": "No extra files.",
        "art_checker.extra_more": "\n… and {count} more",
        "art_checker.preview_idle": "Select an art to preview.",
        "art_checker.preview_missing": "Missing: {name}\nExpected: {path}",
        "art_checker.preview_missing_file": "File listed in JSON scan but not found on disk.",
        "art_checker.preview_load_error": "Could not load preview image.",
        "art_checker.warn_json": "Select a valid prompt book JSON file.",
        "art_checker.scan_done": (
            "Scan complete — present: {present}, missing: {missing}, extra: {extra}"
        ),
        "art_checker.copied_one": "Copied: {name}",
        "art_checker.copied_missing": "Copied {count} missing name(s)",
        "art_checker.grid_hint": (
            "Click to select · double-click to copy name · hover for preview · "
            "scroll wheel on stacked tiles to browse variants"
        ),
        "art_checker.variants_wheel": (
            "{current}/{count} variants — scroll wheel to browse"
        ),
        "art_checker.grid_empty": "No arts to show.",
        "art_checker.grid_count": "{count} arts · OK: {present} · MISS: {missing}",
        "art_checker.grid_count_selected": (
            "{count} arts · OK: {present} · MISS: {missing} · selected: {selected}"
        ),
        "art_checker.tile_missing": "MISSING",
        "images.input": "Input (images):",
        "images.output": "Output (images):",
        "images.group_compress": "Image compression",
        "images.pack_name": "Pack name:",
        "images.pack_placeholder": "e.g. frieren_missionary",
        "images.keep_original_name": "Keep original filenames",
        "images.keep_original_name_tip": (
            "Ignores pack name when compressing. Duplicates get _001, _002… "
            "starting at 1; any old numeric suffix in the input name is reset."
        ),
        "images.jpeg_quality": "JPEG quality:",
        "images.max_side": "Max side (px):",
        "images.workers": "Worker threads:",
        "images.workers_tip": "Parallel processing. On this PC: {cpus} logical cores.",
        "images.group_pdf": "PDF",
        "images.pdf_source": "Image source:",
        "images.pdf_source_input": "Input folder",
        "images.pdf_source_output": "Output folder",
        "images.pdf_dpi_tip": "DPI affects PDF size and page detail.",
        "images.btn_compress": "Compress & strip metadata",
        "images.btn_pdf": "Build PDF",
        "images.hint": (
            "Compression: PNG/JPG → JPEG, no ComfyUI prompts. PDF: all images from the "
            "selected folder into one file (pack_name.pdf). Author — Settings → Author & metadata."
        ),
        "images.warn_pack_name": "Enter a pack name.",
        "images.warn_input": "Select an input folder.",
        "images.warn_output": "Select an output folder.",
        "images.warn_no_images": "No images to process.",
        "images.warn_pdf_source": "Select a source folder for PDF.",
        "images.warn_pdf_output": "Select an output folder for PDF.",
        "images.not_found": "No images found.",
        "images.done": "Processed: {done} of {total}\nFolder: {folder}",
        "images.pdf_done": "PDF created: {pages} pages\n{path}",
        "pixiv.files_group": "Artworks for cover (max. 3)",
        "pixiv.layout_group": "Layout",
        "pixiv.template": "Template:",
        "pixiv.canvas": "Canvas (px):",
        "pixiv.padding": "Edge padding:",
        "pixiv.gap": "Gap:",
        "pixiv.crop_fill": "Crop to cell (even grid)",
        "pixiv.frame_px": "Frame (px):",
        "pixiv.frame_color": "Frame color:",
        "pixiv.pick_color": "Pick color…",
        "pixiv.color_dialog": "Frame color",
        "pixiv.status_empty": "Add 1–3 artworks.",
        "pixiv.status_count": "In list: {count} artwork(s)",
        "pixiv.status_layout": "In list: {count} artwork(s) · layout: {layout}",
        "pixiv.preview_empty": "Add 1–3 artworks — preview will appear here",
        "pixiv.preview_error": "Preview error:\n{error}",
        "pixiv.export_group": "Export",
        "pixiv.output": "Output (Pixiv):",
        "pixiv.filename": "File name:",
        "pixiv.btn_export": "Save cover (PNG)",
        "pixiv.hint": (
            "“Crop to cell” fills the slot (edges may be cut). Without it — fit entire "
            "image with white margins. Frame — around each artwork."
        ),
        "pixiv.pick_images": "Choose artworks (multiple allowed)",
        "pixiv.filter_images": "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        "pixiv.no_new_files": "No new files added. Max 3 artworks; duplicates are skipped.",
        "pixiv.warn_no_images": "Add images.",
        "pixiv.warn_output": "Select a folder to save to.",
        "pixiv.file_missing": "File not found:\n{path}",
        "pixiv.export_done": "Cover saved ({layout}, {count} art.):\n{path}",
        "layout.auto": "Auto",
        "layout.single": "1 — full canvas",
        "layout.row_2": "2 — side by side",
        "layout.col_2": "2 — stacked",
        "layout.row_3": "3 — in a row",
        "layout.hero_left": "3 — large left + 2 right",
        "video.input": "Input (video):",
        "video.output": "Output (video):",
        "video.pack_group": "Pack name",
        "video.pack_prefix": "Prefix:",
        "video.pack_placeholder": "e.g. frieren_clips",
        "video.pack_hint": (
            "Selected clips → name_1.webm, name_2.gif … Folders: watermark/, videos/, gif/, ugoira/"
        ),
        "video.wm_group": "Watermark",
        "video.wm_file": "File:",
        "video.wm_height": "Height (% of frame):",
        "video.wm_height_tip": "Watermark height as a fraction of frame height (8% ≈ 86px at 1080p).",
        "video.wm_alpha": "Opacity:",
        "video.wm_pos_x": "Position X:",
        "video.wm_pos_y": "Position Y:",
        "video.btn_watermark": "Apply watermark to video",
        "video.gif_group": "GIF",
        "video.gif_width": "Width (px):",
        "video.btn_gif": "Export GIF",
        "video.conv_group": "Convert",
        "video.format": "Format:",
        "video.compress_level": "Compression:",
        "video.compress_tip": (
            "Used when re-encoding (WebM always; MP4/MOV with “Re-encode video”). "
            "“Near lossless” and “Minimal” preserve visual quality while saving space."
        ),
        "video.compress.maximum": "Maximum",
        "video.compress.maximum_hint": "Smallest file size, visible quality loss",
        "video.compress.high": "High",
        "video.compress.high_hint": "Strong compression, good for previews and web",
        "video.compress.medium": "Medium",
        "video.compress.medium_hint": "Balance of size and quality",
        "video.compress.near_lossless": "Near lossless",
        "video.compress.near_lossless_hint": "High quality, moderate file size — recommended for Patreon",
        "video.compress.minimal": "Minimal",
        "video.compress.minimal_hint": "Highest quality, largest file — virtually no visible loss",
        "video.keep_audio": "Keep audio",
        "video.remove_meta": "Remove metadata",
        "video.reencode": "Re-encode video (slower)",
        "video.parallel_tasks": "Parallel tasks:",
        "video.workers_tip": (
            "On this PC: {cpus} logical cores. Recommended {rec}.\n"
            "Watermark/GIF (VP9): 2–4 · convert without re-encode: 6–8 · with re-encode: 3–4."
        ),
        "video.patch_in_place": "Replace source files (no re-encode)",
        "video.patch_in_place_tip": "Embeds authorship into selected clips in place: ffmpeg -c copy, fast.",
        "video.btn_convert": "Convert",
        "video.btn_metadata": "Embed authorship",
        "video.ugoira_group": "Ugoira (Pixiv)",
        "video.ugoira_chunk": "Chunk length:",
        "video.ugoira_auto_fps": "Auto FPS for Pixiv (≤150 frames/chunk)",
        "video.ugoira_fps": "Frame FPS:",
        "video.ugoira_max_frames": "Max frames:",
        "video.ugoira_jpeg_quality": "JPEG quality:",
        "video.ugoira_auto_size": "Auto ≤30 MB per ugoira (Pixiv)",
        "video.ugoira_limit": "Ugoira limit:",
        "video.ugoira_limit_tip": (
            "Pixiv limit per ugoira (ZIP of frames). Quality and resolution are reduced automatically if exceeded."
        ),
        "video.ugoira_max_width": "Max width:",
        "video.ugoira_max_width_tip": "Max frame width when auto-sizing (Pixiv shows ~1200px).",
        "video.ugoira_wm": "Watermark on frames (from block above)",
        "video.ugoira_wm_tip": (
            "Applies the selected PNG watermark to each ugoira JPEG frame. "
            "Pick a file in the Watermark list."
        ),
        "video.ugoira_hint": (
            "Selected clips → ugoira/name_1/, name_2/ … Each frames_XXX is a separate ugoira. "
            "Watermark: enable the checkbox below and pick a PNG in the Watermark block."
        ),
        "video.btn_ugoira": "Export Ugoira",
        "video.hint": (
            "Supports mp4, webm, mov, mkv. Author — Settings → Author & metadata. "
            "Watermark: VP9 webm. GIF: palette. Ugoira: frames + animation.json."
        ),
        "video.warn_pack_name": "Enter a pack name (prefix).",
        "video.warn_output": "Select an output folder.",
        "video.warn_no_video": "No videos to process.",
        "video.warn_wm_png": "Select a PNG watermark.",
        "video.warn_author": "Enable authorship in Settings → Author & metadata.",
        "video.warn_ugoira_wm": (
            "Ugoira watermark is enabled but no PNG is selected.\n"
            "Add a file in the Watermark block above."
        ),
        "video.wm_dialog": "PNG watermark",
        "video.wm_filter": "PNG (*.png);;All files (*.*)",
        "video.ugoira_fps_auto": (
            "Auto: {fps} fps · ~{frames} frames per {chunk} sec (Pixiv limit: {max_frames})"
        ),
        "video.ugoira_fps_manual": (
            "Will use {fps} fps (max {cap} for {max_frames} frames) · ~{est} frames/chunk"
        ),
        "video.ugoira_size_auto": (
            "Target: ≤{max_mb} MB per ugoira · ~{kb} KB/frame at {max_frames} frames"
        ),
        "video.ugoira_size_off": "Auto-size off — only “JPEG quality” is used.",
        "video.done_watermark": "Watermark",
        "video.done_gif": "GIF",
        "video.done_convert": "Convert",
        "video.done_metadata": "Authorship",
        "video.done_batch": "{job}: {done} of {total}\nFolder: {folder}",
        "video.done_ugoira": (
            "Ugoira: {clips} clip(s), {chunks} parts, {frames} frames\n{path}"
        ),
        "censor.input": "Input (video/images):",
        "censor.output": "Output (Pixiv):",
        "censor.pack_group": "Pack name",
        "censor.pack_prefix": "Prefix:",
        "censor.pack_placeholder": "e.g. touhou_clips",
        "censor.group": "Censor",
        "censor.block_default": "Pixel size (default):",
        "censor.block_tip": "Default mosaic size in the editor. Pixiv usually needs 12–24.",
        "censor.btn_editor": "Censor editor…",
        "censor.btn_export": "Export with censor → pixiv/",
        "censor.hint": (
            "1) Select file(s) — Ctrl+click for several · 2) “Censor editor” — lasso each "
            "(←/→ between files) · 3) “Export” → pixiv/. "
            "Videos first in the grid, then images."
        ),
        "censor.grid_hint": (
            "Videos first, then images. Ctrl+click or Shift+click to select several; "
            "hover for preview."
        ),
        "censor.warn_select_item": "Select at least one video or image.",
        "censor.editor_prev": "← Previous",
        "censor.editor_next": "Next →",
        "censor.editor_nav": "File {cur} of {total}",
        "censor.editor_title_batch": "Censor — {name} ({cur}/{total})",
        "censor.badge_image": "IMG",
        "censor.no_media": "No videos or images",
        "censor.media_count": "Videos: {videos}, images: {images}",
        "censor.media_count_selected": (
            "Videos: {videos}, images: {images}, selected {selected}"
        ),
        "censor.warn_pack_name": "Enter a pack name (prefix).",
        "censor.warn_one_item": "Select one video or image for the censor editor.",
        "censor.warn_no_media": "No videos or images to export.",
        "censor.warn_output": "Select an output folder.",
        "censor.missing_zones": (
            "{count} file(s) have no censor zones ({names}{extra}).\n"
            "Continue and skip them?"
        ),
        "censor.and_more": " and {n} more",
        "censor.done": "Export: {done} of {total}\n{path}",
        "censor.editor_title": "Censor — {name}",
        "censor.editor_hint": (
            "Hold the left mouse button and outline the area (lasso). "
            "The contour closes automatically. Zones apply to the entire video clip "
            "or the full image."
        ),
        "censor.editor_frame": "Frame:",
        "censor.editor_block": "Pixel size:",
        "censor.editor_block_tip": "Larger — coarser mosaic (typically 12–24 for Pixiv).",
        "censor.editor_zones": "Zones:",
        "censor.editor_remove": "Remove zone",
        "censor.editor_clear": "Clear all",
        "censor.editor_clear_confirm": "Remove all censor zones for this file?",
        "censor.editor_need_zone": "Add at least one zone (lasso on the frame).",
        "censor.editor_frame_fail": "Could not load frame:\n{error}",
        "censor.zone_item": "#{n}: {w}×{h} @ ({x}, {y}), pixel {block}",
        "censor.zone_item_lasso": "#{n}: lasso ({points} pts), pixel {block}",
        "author.title": "Author & metadata",
        "author.intro": (
            "These fields are written to JPEG (EXIF), PDF, and video (mp4/webm): author, "
            "copyright, description, Patreon link. Old ComfyUI/A1111 metadata is removed on export."
        ),
        "author.enabled": "Embed author metadata in files",
        "author.name": "Author:",
        "author.name_ph": "Your name or handle",
        "author.website": "Site / Patreon:",
        "author.website_ph": "https://www.patreon.com/your_profile",
        "author.copyright": "Copyright:",
        "author.copyright_ph": "Leave empty — built from name and site",
        "author.description": "Description:",
        "author.description_ph": "e.g. Support me on Patreon",
        "log.error": "Error: {msg}",
        "log.page": "[{cur}/{total}] page: {name}",
        "log.compress_error": "[{cur}/{total}] {name} — error: {error}",
        "log.resized": " resized",
        "log.done": "Done: {done} of {total}",
        "log.errors_count": "Errors: {failed}",
        "log.skipped_failed": "Skipped/failed: {failed}",
        "log.author_suffix": ", author={author}",
        "log.pack_suffix": " | pack «{pack}»",
        "log.batch_header": "{header}{pack} → {folder}/{author}",
        "log.batch_header_inplace": "{header}{author}",
        "log.yes": "yes",
        "log.no": "no",
        "log.meta_remove": "remove",
        "log.meta_keep": "keep",
        "log.censor.start": (
            "Pixiv censor: {videos} video(s), {images} image(s) | pack «{pack}» → pixiv/"
        ),
        "log.censor.saved": "Censor saved: {name} ({zones} zone(s))",
        "log.censor.skip": "[{cur}/{total}] {name} — skip: no zones",
        "log.censor.item": (
            "[{cur}/{total}] {name} ({kind}) → pixiv/{out} ({zones} zone(s))"
        ),
        "log.censor.kind_img": "img",
        "log.censor.kind_vid": "vid",
        "log.censor.no_zones": "no censor zones — open the editor",
        "log.images.compress_start": (
            "Compress: {input} → {output} | {name_note}, quality={quality}, "
            "max={max}px, workers={workers}{selected}{author}"
        ),
        "log.images.name_original": "original filenames",
        "log.images.name_pack": "pack «{pack}»",
        "log.images.selected": ", selected {count} of {total}",
        "log.images.size_summary": (
            "Size: {before:.1f} MB → {after:.1f} MB (−{saved:.1f} MB, {pct:.0f}%)"
        ),
        "log.images.pdf_start": "PDF: {input} → {output} | pages≈{pages}, dpi={dpi}",
        "log.images.pdf_done_log": "PDF ready: {name} | {pages} page(s), {size:.1f} MB",
        "log.video.item_ok": "[{cur}/{total}] {prefix} → {out}",
        "log.video.item_err": "[{cur}/{total}] {name} — error: {error}",
        "log.video.watermark_start": (
            "Watermark: {file} | height={height}%, alpha={alpha}%, compression={compression}"
        ),
        "log.video.gif_start": "GIF: fps={fps}, width={width}px",
        "log.video.metadata_start": "Authorship (copy): {count} file(s) {mode}{pack}",
        "log.video.metadata_inplace": "in place",
        "log.video.convert_start": (
            "Convert → {fmt} | compression={compression} | audio={audio}, metadata={metadata}"
        ),
        "log.video.ugoira_start": (
            "Ugoira: {count} clip(s) | pack «{pack}» → ugoira/ | "
            "chunk={chunk}s, fps={fps}, max={max_frames}{limit}{wm}{author}"
        ),
        "log.video.ugoira_limit": ", limit={mb}MB",
        "log.video.ugoira_wm": ", watermark={file}",
        "log.video.ugoira_item": "Ugoira [{cur}/{total}]: {name} → {folder}/ ({fps} fps)",
        "log.video.ugoira_chunk": (
            "  {folder}/{chunk}: {frames} frames, {size:.1f} MB{quality}{over}"
        ),
        "log.video.ugoira_chunk_q": ", JPEG q={q}",
        "log.video.ugoira_over_limit": " ⚠ over limit",
        "log.video.ugoira_done": (
            "Ugoira ready: {clips} clip(s), {chunks} parts, {frames} frames → {path}"
        ),
        "grid.select_all": "Select all",
        "grid.clear_selection": "Clear selection",
        "grid.loading": "Loading…",
        "grid.loading_count": "Loading {count}…",
        "grid.read_failed": "Could not read",
        "grid.preview_load_failed": "Could not load",
        "grid.no_images": "No images",
        "grid.no_videos": "No videos",
        "grid.image_count": "Images: {count}",
        "grid.image_count_selected": "Images: {count}, selected {selected}",
        "grid.clip_count": "Clips: {count}",
        "grid.clip_count_selected": "Clips: {count}, selected {selected}",
        "grid.hint": (
            "Preview: hover · select: click (one) · Ctrl+click (toggle) · Shift+click (range)"
        ),
        "grid.sort": "Sort:",
        "grid.sort_name": "Name",
        "grid.sort_date": "Date (newest)",
    },
    "ru": {
        "lang.label": "Язык",
        "lang.en": "English",
        "lang.ru": "Русский",
        "lang.ja": "日本語",
        "menu.settings": "Настройки",
        "menu.author_metadata": "Автор и метаданные…",
        "menu.open_log": "Открыть лог сессии…",
        "tab.images": "Изображения",
        "tab.pixiv_preview": "Превью Pixiv",
        "tab.video": "Видео",
        "tab.pixiv_censor": "Pixiv цензура",
        "tab.art_checker": "Проверка артов",
        "common.browse": "Обзор…",
        "common.content_suite": "ContentSuite",
        "common.add": "Добавить…",
        "common.remove": "Убрать",
        "common.save": "Сохранить",
        "common.cancel": "Отмена",
        "common.ok": "ОК",
        "menu.about": "О программе…",
        "about.title": "О программе ContentSuite",
        "about.version": "v{version}",
        "about.body": (
            "<p>Создано: <a href='{author_url}'>{author}</a><br>"
            "<a href='{repo_url}'>Репозиторий на GitHub</a></p>"
            "<p><b>{ai_label}</b><br>"
            "Совместная разработка: {ai_coauthor} · {ai_tool}</p>"
        ),
        "common.dpi": "DPI",
        "common.fps": "FPS",
        "unit.sec": " сек",
        "unit.mb": " МБ",
        "unit.time_sec": "{value:.1f} с",
        "common.not_selected": "(не выбран)",
        "folder.placeholder": "Выберите папку…",
        "folder.dialog": "Выбор папки — {label}",
        "file.placeholder": "Выберите файл…",
        "file.dialog": "Выбор файла — {label}",
        "file.filter_json": "JSON (*.json);;Все (*.*)",
        "art_checker.json": "Книга промптов (JSON):",
        "art_checker.scan_folder": "Папка для сканирования:",
        "art_checker.refresh": "Обновить",
        "art_checker.auto_watch": "Следить за папкой",
        "art_checker.auto_watch_tip": (
            "Автоматически пересканировать при добавлении, удалении или переименовании файлов."
        ),
        "art_checker.filter": "Фильтр:",
        "art_checker.sort": "Сортировка:",
        "art_checker.sort_name": "По имени",
        "art_checker.sort_date": "По дате (новые)",
        "art_checker.sort_missing_first": "Missing сверху",
        "art_checker.search": "Поиск:",
        "art_checker.copy_name": "Копировать имя",
        "art_checker.copy_missing": "Копировать все missing",
        "art_checker.extra_group": "Лишние файлы (нет в JSON)",
        "art_checker.arts_group": "Арты",
        "art_checker.col_index": "#",
        "art_checker.col_status": "Статус",
        "art_checker.col_section": "Секция",
        "art_checker.col_name": "Имя",
        "art_checker.col_files": "Найденные файлы",
        "art_checker.filter_all": "Все",
        "art_checker.filter_missing": "Missing",
        "art_checker.filter_present": "Есть",
        "art_checker.filter_sfw": "sfw",
        "art_checker.filter_nsfw": "nsfw",
        "art_checker.filter_sex": "sex",
        "art_checker.status_present": "OK",
        "art_checker.status_missing": "MISS",
        "art_checker.summary_idle": "Выберите JSON и папку, затем нажмите «Обновить».",
        "art_checker.summary": (
            "JSON: {total} артов · уникальных файлов: {files} · "
            "есть: {present} · нет: {missing} · лишних: {extra}"
        ),
        "art_checker.extra_none": "Лишних файлов нет.",
        "art_checker.extra_more": "\n… и ещё {count}",
        "art_checker.preview_idle": "Выберите арт для превью.",
        "art_checker.preview_missing": "Нет: {name}\nОжидалось: {path}",
        "art_checker.preview_missing_file": "Файл указан в скане, но не найден на диске.",
        "art_checker.preview_load_error": "Не удалось загрузить превью.",
        "art_checker.warn_json": "Выберите корректный JSON с промптами.",
        "art_checker.scan_done": (
            "Скан готов — есть: {present}, нет: {missing}, лишних: {extra}"
        ),
        "art_checker.copied_one": "Скопировано: {name}",
        "art_checker.copied_missing": "Скопировано имён (missing): {count}",
        "art_checker.grid_hint": (
            "Клик — выбрать · двойной клик — копировать имя · наведение — превью · "
            "колёсико на стопке — листать варианты"
        ),
        "art_checker.variants_wheel": (
            "{current}/{count} вариантов — крути колёсико"
        ),
        "art_checker.grid_empty": "Нет артов для отображения.",
        "art_checker.grid_count": "{count} артов · OK: {present} · MISS: {missing}",
        "art_checker.grid_count_selected": (
            "{count} артов · OK: {present} · MISS: {missing} · выбрано: {selected}"
        ),
        "art_checker.tile_missing": "НЕТ",
        "images.input": "Вход (изображения):",
        "images.output": "Выход (изображения):",
        "images.group_compress": "Сжатие изображений",
        "images.pack_name": "Имя пака:",
        "images.pack_placeholder": "например: frieren_missionary",
        "images.keep_original_name": "Сохранять оригинальное имя файла",
        "images.keep_original_name_tip": (
            "Игнорирует «Имя пака» при сжатии. Дубликаты получают суффикс _001, _002… "
            "с 1; старый суффикс во входном имени сбрасывается."
        ),
        "images.jpeg_quality": "JPEG качество:",
        "images.max_side": "Макс. сторона (px):",
        "images.workers": "Потоков (ядер):",
        "images.workers_tip": "Параллельная обработка. На этом ПК: {cpus} логических ядер.",
        "images.group_pdf": "PDF",
        "images.pdf_source": "Источник картинок:",
        "images.pdf_source_input": "Входная папка",
        "images.pdf_source_output": "Выходная папка",
        "images.pdf_dpi_tip": "DPI влияет на размер PDF и детализацию страниц.",
        "images.btn_compress": "Сжать и убрать метаданные",
        "images.btn_pdf": "Собрать PDF",
        "images.hint": (
            "Сжатие: PNG/JPG → JPEG, без промптов ComfyUI. PDF: все картинки из выбранной "
            "папки в один файл (имя_пака.pdf). Автор — в «Настройки → Автор и метаданные»."
        ),
        "images.warn_pack_name": "Укажите имя пака.",
        "images.warn_input": "Укажите входную папку.",
        "images.warn_output": "Укажите выходную папку.",
        "images.warn_no_images": "Нет изображений для обработки.",
        "images.warn_pdf_source": "Укажите папку-источник для PDF.",
        "images.warn_pdf_output": "Укажите выходную папку для PDF.",
        "images.not_found": "Изображения не найдены.",
        "images.done": "Обработано: {done} из {total}\nПапка: {folder}",
        "images.pdf_done": "PDF создан: {pages} страниц\n{path}",
        "pixiv.files_group": "Арты для обложки (макс. 3)",
        "pixiv.layout_group": "Раскладка",
        "pixiv.template": "Шаблон:",
        "pixiv.canvas": "Холст (px):",
        "pixiv.padding": "Отступ края:",
        "pixiv.gap": "Зазор:",
        "pixiv.crop_fill": "Обрезать под ячейку (ровная сетка)",
        "pixiv.frame_px": "Рамка (px):",
        "pixiv.frame_color": "Цвет рамки:",
        "pixiv.pick_color": "Выбрать цвет…",
        "pixiv.color_dialog": "Цвет рамки",
        "pixiv.status_empty": "Добавьте 1–3 арта.",
        "pixiv.status_count": "В списке: {count} арт(ов)",
        "pixiv.status_layout": "В списке: {count} арт(ов) · раскладка: {layout}",
        "pixiv.preview_empty": "Добавьте 1–3 арта — превью появится здесь",
        "pixiv.preview_error": "Ошибка превью:\n{error}",
        "pixiv.export_group": "Экспорт",
        "pixiv.output": "Выход (Pixiv):",
        "pixiv.filename": "Имя файла:",
        "pixiv.btn_export": "Сохранить обложку (PNG)",
        "pixiv.hint": (
            "«Обрезать под ячейку» — арты заполняют слот целиком (края могут срезаться). "
            "Без галочки — вписываются целиком с белыми полями. Рамка — вокруг каждого арта."
        ),
        "pixiv.pick_images": "Выбор артов (можно несколько сразу)",
        "pixiv.filter_images": "Изображения (*.png *.jpg *.jpeg *.webp *.bmp)",
        "pixiv.no_new_files": "Новые файлы не добавлены. Максимум 3 арта, дубликаты пропускаются.",
        "pixiv.warn_no_images": "Добавьте изображения.",
        "pixiv.warn_output": "Укажите папку для сохранения.",
        "pixiv.file_missing": "Файл не найден:\n{path}",
        "pixiv.export_done": "Обложка сохранена ({layout}, {count} арт.):\n{path}",
        "layout.auto": "Авто",
        "layout.single": "1 — на весь холст",
        "layout.row_2": "2 — рядом",
        "layout.col_2": "2 — друг под другом",
        "layout.row_3": "3 — в ряд",
        "layout.hero_left": "3 — крупный слева + 2 справа",
        "video.input": "Вход (видео):",
        "video.output": "Выход (видео):",
        "video.pack_group": "Имя пака",
        "video.pack_prefix": "Префикс:",
        "video.pack_placeholder": "например: frieren_clips",
        "video.pack_hint": (
            "Выбранные ролики → имя_1.webm, имя_2.gif … Папки: watermark/, videos/, gif/, ugoira/"
        ),
        "video.wm_group": "Watermark",
        "video.wm_file": "Файл:",
        "video.wm_height": "Высота (% кадра):",
        "video.wm_height_tip": "Высота watermark как доля высоты кадра (8% ≈ 86px на 1080p).",
        "video.wm_alpha": "Прозрачность:",
        "video.wm_pos_x": "Позиция X:",
        "video.wm_pos_y": "Позиция Y:",
        "video.btn_watermark": "Наложить watermark на видео",
        "video.gif_group": "GIF",
        "video.gif_width": "Ширина (px):",
        "video.btn_gif": "Экспорт GIF",
        "video.conv_group": "Конвертация",
        "video.format": "Формат:",
        "video.compress_level": "Сжатие:",
        "video.compress_tip": (
            "Применяется при перекодировании (WebM всегда; MP4/MOV с галочкой «Перекодировать»). "
            "«Почти без потерь» и «Минимальное» сохраняют качество и уменьшают размер."
        ),
        "video.compress.maximum": "Максимальное",
        "video.compress.maximum_hint": "Минимальный размер файла, заметная потеря качества",
        "video.compress.high": "Высокое",
        "video.compress.high_hint": "Сильное сжатие, подходит для превью и веба",
        "video.compress.medium": "Среднее",
        "video.compress.medium_hint": "Баланс размера и качества",
        "video.compress.near_lossless": "Почти без потерь",
        "video.compress.near_lossless_hint": "Высокое качество, умеренный размер — рекомендуется для Patreon",
        "video.compress.minimal": "Минимальное",
        "video.compress.minimal_hint": "Максимальное качество, крупный файл — практически без видимых потерь",
        "video.keep_audio": "Сохранить звук",
        "video.remove_meta": "Удалить метаданные",
        "video.reencode": "Перекодировать видео (медленнее)",
        "video.parallel_tasks": "Параллельных задач:",
        "video.workers_tip": (
            "На этом ПК: {cpus} логических ядер. Рекомендуется {rec}.\n"
            "Watermark/GIF (VP9): 2–4 · конвертация без перекодирования: 6–8 · "
            "с перекодированием: 3–4."
        ),
        "video.patch_in_place": "Заменить исходные файлы (без перекодирования)",
        "video.patch_in_place_tip": (
            "Вписывает авторство в выбранные ролики на месте: ffmpeg -c copy, быстро."
        ),
        "video.btn_convert": "Конвертировать",
        "video.btn_metadata": "Вписать авторство",
        "video.ugoira_group": "Ugoira (Pixiv)",
        "video.ugoira_chunk": "Длина куска:",
        "video.ugoira_auto_fps": "Авто FPS под Pixiv (≤150 кадров/кусок)",
        "video.ugoira_fps": "FPS кадров:",
        "video.ugoira_max_frames": "Макс. кадров:",
        "video.ugoira_jpeg_quality": "JPEG качество:",
        "video.ugoira_auto_size": "Авто ≤30 МБ на ugoira (Pixiv)",
        "video.ugoira_limit": "Лимит ugoira:",
        "video.ugoira_limit_tip": (
            "Лимит Pixiv на один ugoira (ZIP с кадрами). При превышении качество и "
            "разрешение снижаются автоматически."
        ),
        "video.ugoira_max_width": "Макс. ширина:",
        "video.ugoira_max_width_tip": "Макс. ширина кадра при авто-размере (Pixiv показывает ~1200px).",
        "video.ugoira_wm": "Watermark на кадрах (из блока выше)",
        "video.ugoira_wm_tip": (
            "Накладывает выбранный PNG watermark на каждый JPEG-кадр ugoira. "
            "Нужен файл в списке Watermark."
        ),
        "video.ugoira_hint": (
            "Выбранные ролики → ugoira/имя_1/, имя_2/ … Каждый frames_XXX — отдельный ugoira. "
            "Watermark: включите галочку ниже и выберите PNG в блоке Watermark."
        ),
        "video.btn_ugoira": "Экспорт Ugoira",
        "video.hint": (
            "Поддерживаются mp4, webm, mov, mkv. Автор — в «Настройки → Автор и метаданные». "
            "Watermark: VP9 webm. GIF: палитра. Ugoira: кадры + animation.json."
        ),
        "video.warn_pack_name": "Укажите имя пака (префикс).",
        "video.warn_output": "Укажите выходную папку.",
        "video.warn_no_video": "Нет видео для обработки.",
        "video.warn_wm_png": "Выберите PNG watermark.",
        "video.warn_author": "Включите авторство в «Настройки → Автор и метаданные».",
        "video.warn_ugoira_wm": (
            "Включён watermark для ugoira, но PNG не выбран.\n"
            "Добавьте файл в блоке Watermark выше."
        ),
        "video.wm_dialog": "PNG watermark",
        "video.wm_filter": "PNG (*.png);;Все файлы (*.*)",
        "video.ugoira_fps_auto": (
            "Авто: {fps} fps · ~{frames} кадров за {chunk} сек (лимит Pixiv: {max_frames})"
        ),
        "video.ugoira_fps_manual": (
            "Будет {fps} fps (макс. {cap} для {max_frames} кадров) · ~{est} кадров/кусок"
        ),
        "video.ugoira_size_auto": (
            "Цель: ≤{max_mb} МБ на ugoira · ~{kb} KB/кадр при {max_frames} кадрах"
        ),
        "video.ugoira_size_off": "Авто-размер выключен — используется только «JPEG качество».",
        "video.done_watermark": "Watermark",
        "video.done_gif": "GIF",
        "video.done_convert": "Конвертация",
        "video.done_metadata": "Авторство",
        "video.done_batch": "{job}: {done} из {total}\nПапка: {folder}",
        "video.done_ugoira": (
            "Ugoira: {clips} ролик(ов), {chunks} частей, {frames} кадров\n{path}"
        ),
        "censor.input": "Вход (видео/картинки):",
        "censor.output": "Выход (Pixiv):",
        "censor.pack_group": "Имя пака",
        "censor.pack_prefix": "Префикс:",
        "censor.pack_placeholder": "например: touhou_clips",
        "censor.group": "Цензура",
        "censor.block_default": "Пиксели (по умолч.):",
        "censor.block_tip": "Размер мозаики по умолчанию в редакторе. Pixiv обычно достаточно 12–24.",
        "censor.btn_editor": "Редактор цензуры…",
        "censor.btn_export": "Экспорт с цензурой → pixiv/",
        "censor.hint": (
            "1) Выберите файл(ы) — Ctrl+клик для нескольких · 2) «Редактор цензуры» — "
            "лассо на каждом (←/→ между файлами) · 3) «Экспорт» → pixiv/. "
            "Сначала видео в сетке, потом картинки."
        ),
        "censor.grid_hint": (
            "Сначала видео, потом картинки. Ctrl+клик или Shift+клик — несколько файлов; "
            "наведите для превью."
        ),
        "censor.warn_select_item": "Выберите хотя бы одно видео или картинку.",
        "censor.editor_prev": "← Назад",
        "censor.editor_next": "Далее →",
        "censor.editor_nav": "Файл {cur} из {total}",
        "censor.editor_title_batch": "Цензура — {name} ({cur}/{total})",
        "censor.badge_image": "IMG",
        "censor.no_media": "Нет видео и картинок",
        "censor.media_count": "Видео: {videos}, картинок: {images}",
        "censor.media_count_selected": (
            "Видео: {videos}, картинок: {images}, выбрано {selected}"
        ),
        "censor.warn_pack_name": "Укажите имя пака (префикс).",
        "censor.warn_one_item": "Выберите одно видео или картинку для редактора цензуры.",
        "censor.warn_no_media": "Нет видео или картинок для экспорта.",
        "censor.warn_output": "Укажите выходную папку.",
        "censor.missing_zones": (
            "У {count} файл(ов) нет зон цензуры ({names}{extra}).\n"
            "Продолжить и пропустить их?"
        ),
        "censor.and_more": " и ещё {n}",
        "censor.done": "Экспорт: {done} из {total}\n{path}",
        "censor.editor_title": "Цензура — {name}",
        "censor.editor_hint": (
            "Зажмите ЛКМ и обведите область (лассо). Контур автоматически замыкается. "
            "Зоны действуют на весь ролик или на всё изображение."
        ),
        "censor.editor_frame": "Кадр:",
        "censor.editor_block": "Размер пикселей:",
        "censor.editor_block_tip": "Чем больше — грубее мозаика (типично 12–24 для Pixiv).",
        "censor.editor_zones": "Зоны:",
        "censor.editor_remove": "Удалить зону",
        "censor.editor_clear": "Очистить все",
        "censor.editor_clear_confirm": "Удалить все зоны цензуры для этого файла?",
        "censor.editor_need_zone": "Добавьте хотя бы одну зону (лассо по кадру).",
        "censor.editor_frame_fail": "Не удалось загрузить кадр:\n{error}",
        "censor.zone_item": "#{n}: {w}×{h} @ ({x}, {y}), пиксель {block}",
        "censor.zone_item_lasso": "#{n}: лассо ({points} точек), пиксель {block}",
        "author.title": "Автор и метаданные",
        "author.intro": (
            "Эти данные записываются в JPEG (EXIF), PDF и видео (mp4/webm): автор, "
            "копирайт, описание, ссылка Patreon. Старые метаданные ComfyUI/A1111 "
            "удаляются при экспорте."
        ),
        "author.enabled": "Добавлять метаданные автора в файлы",
        "author.name": "Автор:",
        "author.name_ph": "Ваш ник или имя",
        "author.website": "Сайт / Patreon:",
        "author.website_ph": "https://www.patreon.com/ваш_профиль",
        "author.copyright": "Копирайт:",
        "author.copyright_ph": "Оставьте пустым — соберётся из имени и сайта",
        "author.description": "Описание:",
        "author.description_ph": "Например: Support me on Patreon",
        "log.error": "Ошибка: {msg}",
        "log.page": "[{cur}/{total}] страница: {name}",
        "log.compress_error": "[{cur}/{total}] {name} — ошибка: {error}",
        "log.resized": " resized",
        "log.done": "Готово: {done} из {total}",
        "log.errors_count": "Ошибок: {failed}",
        "log.skipped_failed": "Пропущено/ошибок: {failed}",
        "log.author_suffix": ", автор={author}",
        "log.pack_suffix": " | пак «{pack}»",
        "log.batch_header": "{header}{pack} → {folder}/{author}",
        "log.batch_header_inplace": "{header}{author}",
        "log.yes": "да",
        "log.no": "нет",
        "log.meta_remove": "удалить",
        "log.meta_keep": "оставить",
        "log.censor.start": (
            "Pixiv цензура: {videos} видео, {images} изображений | пак «{pack}» → pixiv/"
        ),
        "log.censor.saved": "Цензура сохранена: {name} ({zones} зон)",
        "log.censor.skip": "[{cur}/{total}] {name} — пропуск: нет зон",
        "log.censor.item": (
            "[{cur}/{total}] {name} ({kind}) → pixiv/{out} ({zones} зон)"
        ),
        "log.censor.kind_img": "img",
        "log.censor.kind_vid": "vid",
        "log.censor.no_zones": "нет зон цензуры — откройте редактор",
        "log.images.compress_start": (
            "Сжатие: {input} → {output} | {name_note}, quality={quality}, "
            "max={max}px, потоков={workers}{selected}{author}"
        ),
        "log.images.name_original": "оригинальные имена",
        "log.images.name_pack": "пак «{pack}»",
        "log.images.selected": ", выбрано {count} из {total}",
        "log.images.size_summary": (
            "Размер: {before:.1f} MB → {after:.1f} MB (−{saved:.1f} MB, {pct:.0f}%)"
        ),
        "log.images.pdf_start": "PDF: {input} → {output} | страниц≈{pages}, dpi={dpi}",
        "log.images.pdf_done_log": "PDF готов: {name} | {pages} стр., {size:.1f} MB",
        "log.video.item_ok": "[{cur}/{total}] {prefix} → {out}",
        "log.video.item_err": "[{cur}/{total}] {name} — ошибка: {error}",
        "log.video.watermark_start": (
            "Watermark: {file} | высота={height}%, alpha={alpha}%, сжатие={compression}"
        ),
        "log.video.gif_start": "GIF: fps={fps}, ширина={width}px",
        "log.video.metadata_start": "Авторство (copy): {count} файл(ов) {mode}{pack}",
        "log.video.metadata_inplace": "на месте",
        "log.video.convert_start": (
            "Конвертация → {fmt} | сжатие={compression} | звук={audio}, метаданные={metadata}"
        ),
        "log.video.ugoira_start": (
            "Ugoira: {count} ролик(ов) | пак «{pack}» → ugoira/ | "
            "chunk={chunk}s, fps={fps}, max={max_frames}{limit}{wm}{author}"
        ),
        "log.video.ugoira_limit": ", лимит={mb}МБ",
        "log.video.ugoira_wm": ", watermark={file}",
        "log.video.ugoira_item": "Ugoira [{cur}/{total}]: {name} → {folder}/ ({fps} fps)",
        "log.video.ugoira_chunk": (
            "  {folder}/{chunk}: {frames} кадров, {size:.1f} МБ{quality}{over}"
        ),
        "log.video.ugoira_chunk_q": ", JPEG q={q}",
        "log.video.ugoira_over_limit": " ⚠ выше лимита",
        "log.video.ugoira_done": (
            "Ugoira готов: {clips} ролик(ов), {chunks} ugoira-частей, "
            "{frames} кадров → {path}"
        ),
        "grid.select_all": "Выбрать все",
        "grid.clear_selection": "Снять выбор",
        "grid.loading": "загрузка…",
        "grid.loading_count": "Загрузка {count}…",
        "grid.read_failed": "не удалось прочитать",
        "grid.preview_load_failed": "не удалось загрузить",
        "grid.no_images": "Нет изображений",
        "grid.no_videos": "Нет видео",
        "grid.image_count": "Изображений: {count}",
        "grid.image_count_selected": "Изображений: {count}, выбрано {selected}",
        "grid.clip_count": "Роликов: {count}",
        "grid.clip_count_selected": "Роликов: {count}, выбрано {selected}",
        "grid.hint": (
            "Превью: наведение · выбор: клик (один) · Ctrl+клик (добавить/убрать) · "
            "Shift+клик (диапазон)"
        ),
        "grid.sort": "Сортировка:",
        "grid.sort_name": "По имени",
        "grid.sort_date": "По дате (новые)",
    },
    "ja": {
        "lang.label": "言語",
        "lang.en": "English",
        "lang.ru": "Русский",
        "lang.ja": "日本語",
        "menu.settings": "設定",
        "menu.author_metadata": "作者とメタデータ…",
        "menu.open_log": "セッションログを開く…",
        "tab.images": "画像",
        "tab.pixiv_preview": "Pixivプレビュー",
        "tab.video": "動画",
        "tab.pixiv_censor": "Pixivモザイク",
        "tab.art_checker": "作品チェック",
        "common.browse": "参照…",
        "common.content_suite": "ContentSuite",
        "common.add": "追加…",
        "common.remove": "削除",
        "common.save": "保存",
        "common.cancel": "キャンセル",
        "common.ok": "OK",
        "menu.about": "ContentSuiteについて…",
        "about.title": "ContentSuiteについて",
        "about.version": "v{version}",
        "about.body": (
            "<p>作成: <a href='{author_url}'>{author}</a><br>"
            "<a href='{repo_url}'>GitHubリポジトリ</a></p>"
            "<p><b>{ai_label}</b><br>"
            "共同開発: {ai_coauthor} · {ai_tool}</p>"
        ),
        "common.dpi": "DPI",
        "common.fps": "FPS",
        "unit.sec": " 秒",
        "unit.mb": " MB",
        "unit.time_sec": "{value:.1f} 秒",
        "common.not_selected": "（未選択）",
        "folder.placeholder": "フォルダを選択…",
        "folder.dialog": "フォルダ選択 — {label}",
        "file.placeholder": "ファイルを選択…",
        "file.dialog": "ファイル選択 — {label}",
        "file.filter_json": "JSON (*.json);;すべて (*.*)",
        "art_checker.json": "プロンプト JSON:",
        "art_checker.scan_folder": "スキャン先フォルダ:",
        "art_checker.refresh": "更新",
        "art_checker.auto_watch": "フォルダの変更を監視",
        "art_checker.auto_watch_tip": (
            "スキャン先フォルダでファイルの追加・削除・名前変更があったら自動で再スキャンします。"
        ),
        "art_checker.filter": "フィルター:",
        "art_checker.sort": "並べ替え:",
        "art_checker.sort_name": "名前",
        "art_checker.sort_date": "日付（新しい順）",
        "art_checker.sort_missing_first": "不足を先に",
        "art_checker.search": "検索:",
        "art_checker.copy_name": "選択名をコピー",
        "art_checker.copy_missing": "不足分をすべてコピー",
        "art_checker.extra_group": "余分なファイル（JSONにない）",
        "art_checker.arts_group": "作品一覧",
        "art_checker.col_index": "#",
        "art_checker.col_status": "状態",
        "art_checker.col_section": "区分",
        "art_checker.col_name": "名前",
        "art_checker.col_files": "見つかったファイル",
        "art_checker.filter_all": "すべて",
        "art_checker.filter_missing": "不足",
        "art_checker.filter_present": "あり",
        "art_checker.filter_sfw": "sfw",
        "art_checker.filter_nsfw": "nsfw",
        "art_checker.filter_sex": "sex",
        "art_checker.status_present": "OK",
        "art_checker.status_missing": "MISS",
        "art_checker.summary_idle": "JSONとフォルダを選び、「更新」を押してください。",
        "art_checker.summary": (
            "JSON: {total} 件 · ユニークファイル: {files} · "
            "あり: {present} · 不足: {missing} · 余分: {extra}"
        ),
        "art_checker.extra_none": "余分なファイルはありません。",
        "art_checker.extra_more": "\n… 他 {count} 件",
        "art_checker.preview_idle": "作品を選択するとプレビューが表示されます。",
        "art_checker.preview_missing": "不足: {name}\n想定パス: {path}",
        "art_checker.preview_missing_file": "スキャン結果にあるがディスク上に見つかりません。",
        "art_checker.preview_load_error": "プレビューを読み込めませんでした。",
        "art_checker.warn_json": "有効なプロンプト JSON を選択してください。",
        "art_checker.scan_done": (
            "スキャン完了 — あり: {present}, 不足: {missing}, 余分: {extra}"
        ),
        "art_checker.copied_one": "コピーしました: {name}",
        "art_checker.copied_missing": "不足 {count} 件の名前をコピーしました",
        "art_checker.grid_hint": (
            "クリックで選択 · ダブルクリックで名前コピー · ホバーでプレビュー · "
            "重なりタイルでホイール切替"
        ),
        "art_checker.variants_wheel": (
            "{current}/{count} 件 — ホイールで切替"
        ),
        "art_checker.grid_empty": "表示する作品がありません。",
        "art_checker.grid_count": "{count} 件 · OK: {present} · MISS: {missing}",
        "art_checker.grid_count_selected": (
            "{count} 件 · OK: {present} · MISS: {missing} · 選択: {selected}"
        ),
        "art_checker.tile_missing": "不足",
        "images.input": "入力（画像）:",
        "images.output": "出力（画像）:",
        "images.group_compress": "画像圧縮",
        "images.pack_name": "パック名:",
        "images.pack_placeholder": "例: frieren_missionary",
        "images.keep_original_name": "元のファイル名を保持",
        "images.keep_original_name_tip": (
            "圧縮時にパック名を無視します。重複には _001、_002… と付与（1から）。"
            "入力名の古い番号サフィックスはリセットされます。"
        ),
        "images.jpeg_quality": "JPEG品質:",
        "images.max_side": "最大辺 (px):",
        "images.workers": "ワーカー数:",
        "images.workers_tip": "並列処理。このPC: {cpus} 論理コア。",
        "images.group_pdf": "PDF",
        "images.pdf_source": "画像ソース:",
        "images.pdf_source_input": "入力フォルダ",
        "images.pdf_source_output": "出力フォルダ",
        "images.pdf_dpi_tip": "DPIはPDFサイズとページの細部に影響します。",
        "images.btn_compress": "圧縮してメタデータ削除",
        "images.btn_pdf": "PDFを作成",
        "images.hint": (
            "圧縮: PNG/JPG → JPEG、ComfyUIプロンプトなし。PDF: 選択フォルダの全画像を"
            "1ファイルに（パック名.pdf）。作者 — 設定 → 作者とメタデータ。"
        ),
        "images.warn_pack_name": "パック名を入力してください。",
        "images.warn_input": "入力フォルダを指定してください。",
        "images.warn_output": "出力フォルダを指定してください。",
        "images.warn_no_images": "処理する画像がありません。",
        "images.warn_pdf_source": "PDFのソースフォルダを指定してください。",
        "images.warn_pdf_output": "PDFの出力フォルダを指定してください。",
        "images.not_found": "画像が見つかりません。",
        "images.done": "処理完了: {done} / {total}\nフォルダ: {folder}",
        "images.pdf_done": "PDF作成: {pages} ページ\n{path}",
        "pixiv.files_group": "カバー用イラスト（最大3）",
        "pixiv.layout_group": "レイアウト",
        "pixiv.template": "テンプレート:",
        "pixiv.canvas": "キャンバス (px):",
        "pixiv.padding": "余白:",
        "pixiv.gap": "間隔:",
        "pixiv.crop_fill": "セルに合わせてトリミング",
        "pixiv.frame_px": "枠 (px):",
        "pixiv.frame_color": "枠の色:",
        "pixiv.pick_color": "色を選択…",
        "pixiv.color_dialog": "枠の色",
        "pixiv.status_empty": "イラストを1〜3枚追加してください。",
        "pixiv.status_count": "リスト: {count} 枚",
        "pixiv.status_layout": "リスト: {count} 枚 · レイアウト: {layout}",
        "pixiv.preview_empty": "イラストを1〜3枚追加 — プレビューがここに表示されます",
        "pixiv.preview_error": "プレビューエラー:\n{error}",
        "pixiv.export_group": "エクスポート",
        "pixiv.output": "出力 (Pixiv):",
        "pixiv.filename": "ファイル名:",
        "pixiv.btn_export": "カバーを保存 (PNG)",
        "pixiv.hint": (
            "「セルに合わせてトリミング」— スロット全体を埋めます（端が切れる場合あり）。"
            "オフ — 全体を白余白付きで収めます。枠 — 各イラストの周囲。"
        ),
        "pixiv.pick_images": "イラストを選択（複数可）",
        "pixiv.filter_images": "画像 (*.png *.jpg *.jpeg *.webp *.bmp)",
        "pixiv.no_new_files": "新しいファイルは追加されませんでした。最大3枚、重複はスキップ。",
        "pixiv.warn_no_images": "画像を追加してください。",
        "pixiv.warn_output": "保存先フォルダを指定してください。",
        "pixiv.file_missing": "ファイルが見つかりません:\n{path}",
        "pixiv.export_done": "カバー保存 ({layout}, {count} 枚):\n{path}",
        "layout.auto": "自動",
        "layout.single": "1 — 全面",
        "layout.row_2": "2 — 横並び",
        "layout.col_2": "2 — 縦並び",
        "layout.row_3": "3 — 横一列",
        "layout.hero_left": "3 — 左大 + 右2",
        "video.input": "入力（動画）:",
        "video.output": "出力（動画）:",
        "video.pack_group": "パック名",
        "video.pack_prefix": "プレフィックス:",
        "video.pack_placeholder": "例: frieren_clips",
        "video.pack_hint": (
            "選択クリップ → name_1.webm, name_2.gif … フォルダ: watermark/, videos/, gif/, ugoira/"
        ),
        "video.wm_group": "ウォーターマーク",
        "video.wm_file": "ファイル:",
        "video.wm_height": "高さ（フレーム%）:",
        "video.wm_height_tip": "フレーム高さに対する比率（8% ≈ 1080pで86px）。",
        "video.wm_alpha": "不透明度:",
        "video.wm_pos_x": "位置 X:",
        "video.wm_pos_y": "位置 Y:",
        "video.btn_watermark": "動画にウォーターマーク",
        "video.gif_group": "GIF",
        "video.gif_width": "幅 (px):",
        "video.btn_gif": "GIFエクスポート",
        "video.conv_group": "変換",
        "video.format": "形式:",
        "video.compress_level": "圧縮:",
        "video.compress_tip": (
            "再エンコード時に適用（WebMは常時、MP4/MOVは「再エンコード」オン時）。"
            "「ほぼ可逆」「最小」は画質を保ちつつサイズ削減。"
        ),
        "video.compress.maximum": "最大",
        "video.compress.maximum_hint": "最小ファイル、画質低下が目立つ",
        "video.compress.high": "高",
        "video.compress.high_hint": "強い圧縮、プレビュー・Web向け",
        "video.compress.medium": "中",
        "video.compress.medium_hint": "サイズと画質のバランス",
        "video.compress.near_lossless": "ほぼ可逆",
        "video.compress.near_lossless_hint": "高画質・中サイズ — Patreon向け推奨",
        "video.compress.minimal": "最小",
        "video.compress.minimal_hint": "最高画質・大きいファイル — 目に見える劣化ほぼなし",
        "video.keep_audio": "音声を保持",
        "video.remove_meta": "メタデータ削除",
        "video.reencode": "再エンコード（遅い）",
        "video.parallel_tasks": "並列タスク:",
        "video.workers_tip": (
            "このPC: {cpus} 論理コア。推奨 {rec}。\n"
            "Watermark/GIF (VP9): 2–4 · 再エンコードなし: 6–8 · あり: 3–4。"
        ),
        "video.patch_in_place": "元ファイルを置換（再エンコードなし）",
        "video.patch_in_place_tip": "選択クリップにその場で作者情報を埋め込み: ffmpeg -c copy、高速。",
        "video.btn_convert": "変換",
        "video.btn_metadata": "作者情報を埋め込み",
        "video.ugoira_group": "Ugoira (Pixiv)",
        "video.ugoira_chunk": "チャンク長:",
        "video.ugoira_auto_fps": "Pixiv用自動FPS（≤150フレーム/チャンク）",
        "video.ugoira_fps": "フレームFPS:",
        "video.ugoira_max_frames": "最大フレーム:",
        "video.ugoira_jpeg_quality": "JPEG品質:",
        "video.ugoira_auto_size": "自動 ≤30MB/ugoira (Pixiv)",
        "video.ugoira_limit": "Ugoira上限:",
        "video.ugoira_limit_tip": "Pixivの1 ugoira上限（フレームZIP）。超過時は品質・解像度を自動低下。",
        "video.ugoira_max_width": "最大幅:",
        "video.ugoira_max_width_tip": "自動サイズ時の最大フレーム幅（Pixivは約1200px）。",
        "video.ugoira_wm": "フレームにWM（上のブロックから）",
        "video.ugoira_wm_tip": "選択PNGを各ugoira JPEGフレームに適用。Watermarkリストにファイルが必要。",
        "video.ugoira_hint": (
            "選択クリップ → ugoira/name_1/, name_2/ … 各 frames_XXX が別 ugoira。"
            "WM: 下のチェックをオンにし Watermark でPNGを選択。"
        ),
        "video.btn_ugoira": "Ugoiraエクスポート",
        "video.hint": (
            "mp4, webm, mov, mkv 対応。作者 — 設定 → 作者とメタデータ。"
            "Watermark: VP9 webm。GIF: パレット。Ugoira: フレーム + animation.json。"
        ),
        "video.warn_pack_name": "パック名（プレフィックス）を入力してください。",
        "video.warn_output": "出力フォルダを指定してください。",
        "video.warn_no_video": "処理する動画がありません。",
        "video.warn_wm_png": "PNGウォーターマークを選択してください。",
        "video.warn_author": "設定 → 作者とメタデータで作者情報を有効にしてください。",
        "video.warn_ugoira_wm": (
            "UgoiraのWMが有効ですがPNGが未選択です。\n"
            "上のWatermarkブロックでファイルを追加してください。"
        ),
        "video.wm_dialog": "PNGウォーターマーク",
        "video.wm_filter": "PNG (*.png);;すべてのファイル (*.*)",
        "video.ugoira_fps_auto": (
            "自動: {fps} fps · 約{frames}フレーム/{chunk}秒 (Pixiv上限: {max_frames})"
        ),
        "video.ugoira_fps_manual": (
            "{fps} fps を使用 (最大 {cap}、{max_frames}フレーム) · 約{est}フレーム/チャンク"
        ),
        "video.ugoira_size_auto": (
            "目標: ≤{max_mb}MB/ugoira · 約{kb}KB/フレーム（{max_frames}フレーム時）"
        ),
        "video.ugoira_size_off": "自動サイズオフ — 「JPEG品質」のみ使用。",
        "video.done_watermark": "Watermark",
        "video.done_gif": "GIF",
        "video.done_convert": "変換",
        "video.done_metadata": "作者情報",
        "video.done_batch": "{job}: {done} / {total}\nフォルダ: {folder}",
        "video.done_ugoira": (
            "Ugoira: {clips} 本, {chunks} パート, {frames} フレーム\n{path}"
        ),
        "censor.input": "入力（動画/画像）:",
        "censor.output": "出力 (Pixiv):",
        "censor.pack_group": "パック名",
        "censor.pack_prefix": "プレフィックス:",
        "censor.pack_placeholder": "例: touhou_clips",
        "censor.group": "モザイク",
        "censor.block_default": "ピクセルサイズ（既定）:",
        "censor.block_tip": "エディタの既定モザイクサイズ。Pixivは通常12–24。",
        "censor.btn_editor": "モザイクエディタ…",
        "censor.btn_export": "モザイク付きエクスポート → pixiv/",
        "censor.hint": (
            "1) ファイル選択 — 複数はCtrl+クリック · 2) 「モザイクエディタ」— 各ファイルにラッソ "
            "（←/→で切替） · 3) 「エクスポート」→ pixiv/。グリッドは動画→画像の順。"
        ),
        "censor.grid_hint": (
            "動画→画像の順。Ctrl+クリックまたはShift+クリックで複数選択、ホバーでプレビュー。"
        ),
        "censor.warn_select_item": "動画または画像を1つ以上選択してください。",
        "censor.editor_prev": "← 前へ",
        "censor.editor_next": "次へ →",
        "censor.editor_nav": "ファイル {cur} / {total}",
        "censor.editor_title_batch": "モザイク — {name} ({cur}/{total})",
        "censor.badge_image": "IMG",
        "censor.no_media": "動画・画像なし",
        "censor.media_count": "動画: {videos}、画像: {images}",
        "censor.media_count_selected": (
            "動画: {videos}、画像: {images}、選択 {selected}"
        ),
        "censor.warn_pack_name": "パック名（プレフィックス）を入力してください。",
        "censor.warn_one_item": "モザイクエディタ用に動画または画像を1つ選択してください。",
        "censor.warn_no_media": "エクスポートする動画・画像がありません。",
        "censor.warn_output": "出力フォルダを指定してください。",
        "censor.missing_zones": (
            "{count} 件にモザイクゾーンがありません ({names}{extra})。\n"
            "続行してスキップしますか？"
        ),
        "censor.and_more": " 他{n}本",
        "censor.done": "エクスポート: {done} / {total}\n{path}",
        "censor.editor_title": "モザイク — {name}",
        "censor.editor_hint": (
            "左クリック長押しで範囲をなぞる（ラッソ）。輪郭は自動で閉じます。"
            "ゾーンは動画クリップ全体または画像全体に適用。"
        ),
        "censor.editor_frame": "フレーム:",
        "censor.editor_block": "ピクセルサイズ:",
        "censor.editor_block_tip": "大きいほど粗いモザイク（Pixivは通常12–24）。",
        "censor.editor_zones": "ゾーン:",
        "censor.editor_remove": "ゾーン削除",
        "censor.editor_clear": "すべてクリア",
        "censor.editor_clear_confirm": "このファイルのモザイクゾーンをすべて削除しますか？",
        "censor.editor_need_zone": "ゾーンを1つ以上追加（ラッソでなぞる）。",
        "censor.editor_frame_fail": "フレームを読み込めませんでした:\n{error}",
        "censor.zone_item": "#{n}: {w}×{h} @ ({x}, {y}), ピクセル {block}",
        "censor.zone_item_lasso": "#{n}: ラッソ ({points}点), ピクセル {block}",
        "author.title": "作者とメタデータ",
        "author.intro": (
            "JPEG (EXIF)、PDF、動画 (mp4/webm) に書き込み: 作者、著作権、説明、Patreonリンク。"
            "ComfyUI/A1111の古いメタデータはエクスポート時に削除。"
        ),
        "author.enabled": "ファイルに作者メタデータを追加",
        "author.name": "作者:",
        "author.name_ph": "名前またはハンドル",
        "author.website": "サイト / Patreon:",
        "author.website_ph": "https://www.patreon.com/your_profile",
        "author.copyright": "著作権:",
        "author.copyright_ph": "空欄 — 名前とサイトから生成",
        "author.description": "説明:",
        "author.description_ph": "例: Support me on Patreon",
        "log.error": "エラー: {msg}",
        "log.page": "[{cur}/{total}] ページ: {name}",
        "log.compress_error": "[{cur}/{total}] {name} — エラー: {error}",
        "log.resized": " resized",
        "log.done": "完了: {done} / {total}",
        "log.errors_count": "エラー: {failed}",
        "log.skipped_failed": "スキップ/エラー: {failed}",
        "log.author_suffix": ", 作者={author}",
        "log.pack_suffix": " | パック «{pack}»",
        "log.batch_header": "{header}{pack} → {folder}/{author}",
        "log.batch_header_inplace": "{header}{author}",
        "log.yes": "あり",
        "log.no": "なし",
        "log.meta_remove": "削除",
        "log.meta_keep": "保持",
        "log.censor.start": (
            "Pixivモザイク: 動画 {videos} 本、画像 {images} 枚 | パック «{pack}» → pixiv/"
        ),
        "log.censor.saved": "モザイク保存: {name} ({zones} ゾーン)",
        "log.censor.skip": "[{cur}/{total}] {name} — スキップ: ゾーンなし",
        "log.censor.item": (
            "[{cur}/{total}] {name} ({kind}) → pixiv/{out} ({zones} ゾーン)"
        ),
        "log.censor.kind_img": "img",
        "log.censor.kind_vid": "vid",
        "log.censor.no_zones": "モザイクゾーンなし — エディタを開いてください",
        "log.images.compress_start": (
            "圧縮: {input} → {output} | {name_note}, quality={quality}, "
            "max={max}px, workers={workers}{selected}{author}"
        ),
        "log.images.name_original": "元のファイル名",
        "log.images.name_pack": "パック «{pack}»",
        "log.images.selected": ", 選択 {count} / {total}",
        "log.images.size_summary": (
            "サイズ: {before:.1f} MB → {after:.1f} MB (−{saved:.1f} MB, {pct:.0f}%)"
        ),
        "log.images.pdf_start": "PDF: {input} → {output} | ページ≈{pages}, dpi={dpi}",
        "log.images.pdf_done_log": "PDF完了: {name} | {pages} ページ, {size:.1f} MB",
        "log.video.item_ok": "[{cur}/{total}] {prefix} → {out}",
        "log.video.item_err": "[{cur}/{total}] {name} — エラー: {error}",
        "log.video.watermark_start": (
            "Watermark: {file} | 高さ={height}%, alpha={alpha}%, 圧縮={compression}"
        ),
        "log.video.gif_start": "GIF: fps={fps}, 幅={width}px",
        "log.video.metadata_start": "作者情報 (copy): {count} ファイル {mode}{pack}",
        "log.video.metadata_inplace": "その場",
        "log.video.convert_start": (
            "変換 → {fmt} | 圧縮={compression} | 音声={audio}, メタデータ={metadata}"
        ),
        "log.video.ugoira_start": (
            "Ugoira: {count} 本 | パック «{pack}» → ugoira/ | "
            "chunk={chunk}s, fps={fps}, max={max_frames}{limit}{wm}{author}"
        ),
        "log.video.ugoira_limit": ", 上限={mb}MB",
        "log.video.ugoira_wm": ", watermark={file}",
        "log.video.ugoira_item": "Ugoira [{cur}/{total}]: {name} → {folder}/ ({fps} fps)",
        "log.video.ugoira_chunk": (
            "  {folder}/{chunk}: {frames} フレーム, {size:.1f} MB{quality}{over}"
        ),
        "log.video.ugoira_chunk_q": ", JPEG q={q}",
        "log.video.ugoira_over_limit": " ⚠ 上限超過",
        "log.video.ugoira_done": (
            "Ugoira完了: {clips} 本, {chunks} パート, {frames} フレーム → {path}"
        ),
        "grid.select_all": "すべて選択",
        "grid.clear_selection": "選択解除",
        "grid.loading": "読み込み中…",
        "grid.loading_count": "{count} 件を読み込み中…",
        "grid.read_failed": "読み取り失敗",
        "grid.preview_load_failed": "読み込み失敗",
        "grid.no_images": "画像なし",
        "grid.no_videos": "動画なし",
        "grid.image_count": "画像: {count}",
        "grid.image_count_selected": "画像: {count}、選択 {selected}",
        "grid.clip_count": "クリップ: {count}",
        "grid.clip_count_selected": "クリップ: {count}、選択 {selected}",
        "grid.hint": (
            "プレビュー: ホバー · 選択: クリック（1件） · Ctrl+クリック（追加/解除） · "
            "Shift+クリック（範囲）"
        ),
        "grid.sort": "並べ替え:",
        "grid.sort_name": "名前",
        "grid.sort_date": "日付（新しい順）",
    },
}

SUPPORTED_LANGUAGES: tuple[tuple[str, str], ...] = (
    ("en", "lang.en"),
    ("ru", "lang.ru"),
    ("ja", "lang.ja"),
)