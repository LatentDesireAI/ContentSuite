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
        "common.browse": "Browse…",
        "common.content_suite": "ContentSuite",
        "common.add": "Add…",
        "common.remove": "Remove",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.ok": "OK",
        "menu.about": "About ContentSuite…",
        "about.title": "About ContentSuite",
        "about.body": (
            "<h2 style='margin-top:0'>{app}</h2>"
            "<p style='color:#666'>v{version}</p>"
            "<p>Created by <a href='{author_url}'>{author}</a><br>"
            "<a href='{repo_url}'>GitHub repository</a></p>"
            "<p><b>{ai_label}</b><br>"
            "Co-development: {ai_coauthor} · {ai_tool}</p>"
        ),
        "common.dpi": "DPI",
        "common.fps": "FPS",
        "common.not_selected": "(not selected)",
        "folder.placeholder": "Choose a folder…",
        "folder.dialog": "Choose folder — {label}",
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
        "censor.input": "Input (video):",
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
            "1) Select a clip · 2) “Censor editor” — drag over the area · "
            "3) “Export” → pixiv/name_1.mp4. Zones are static for the whole clip."
        ),
        "censor.warn_pack_name": "Enter a pack name (prefix).",
        "censor.warn_one_clip": "Select one clip for the censor editor.",
        "censor.warn_no_video": "No videos to export.",
        "censor.warn_output": "Select an output folder.",
        "censor.missing_zones": (
            "{count} clip(s) have no censor zones ({names}{extra}).\n"
            "Continue and skip them?"
        ),
        "censor.and_more": " and {n} more",
        "censor.done": "Export: {done} of {total}\n{path}",
        "censor.editor_title": "Censor — {name}",
        "censor.editor_hint": (
            "Drag over the area to censor. Zones apply to the entire clip (static censor)."
        ),
        "censor.editor_frame": "Frame:",
        "censor.editor_block": "Pixel size:",
        "censor.editor_block_tip": "Larger — coarser mosaic (typically 12–24 for Pixiv).",
        "censor.editor_zones": "Zones:",
        "censor.editor_remove": "Remove zone",
        "censor.editor_clear": "Clear all",
        "censor.editor_clear_confirm": "Remove all censor zones for this clip?",
        "censor.editor_need_zone": "Add at least one zone (drag on the frame).",
        "censor.editor_frame_fail": "Could not load frame:\n{error}",
        "censor.zone_item": "#{n}: {w}×{h} @ ({x}, {y}), pixel {block}",
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
        "common.browse": "Обзор…",
        "common.content_suite": "ContentSuite",
        "common.add": "Добавить…",
        "common.remove": "Убрать",
        "common.save": "Сохранить",
        "common.cancel": "Отмена",
        "common.ok": "ОК",
        "menu.about": "О программе…",
        "about.title": "О программе ContentSuite",
        "about.body": (
            "<h2 style='margin-top:0'>{app}</h2>"
            "<p style='color:#666'>v{version}</p>"
            "<p>Создано: <a href='{author_url}'>{author}</a><br>"
            "<a href='{repo_url}'>Репозиторий на GitHub</a></p>"
            "<p><b>{ai_label}</b><br>"
            "Совместная разработка: {ai_coauthor} · {ai_tool}</p>"
        ),
        "common.dpi": "DPI",
        "common.fps": "FPS",
        "common.not_selected": "(не выбран)",
        "folder.placeholder": "Выберите папку…",
        "folder.dialog": "Выбор папки — {label}",
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
        "censor.input": "Вход (видео):",
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
            "1) Выберите ролик · 2) «Редактор цензуры» — потяните мышью по области · "
            "3) «Экспорт» → папка pixiv/имя_1.mp4. Зоны статичны на весь ролик."
        ),
        "censor.warn_pack_name": "Укажите имя пака (префикс).",
        "censor.warn_one_clip": "Выберите один ролик для редактора цензуры.",
        "censor.warn_no_video": "Нет видео для экспорта.",
        "censor.warn_output": "Укажите выходную папку.",
        "censor.missing_zones": (
            "У {count} ролик(ов) нет зон цензуры ({names}{extra}).\n"
            "Продолжить и пропустить их?"
        ),
        "censor.and_more": " и ещё {n}",
        "censor.done": "Экспорт: {done} из {total}\n{path}",
        "censor.editor_title": "Цензура — {name}",
        "censor.editor_hint": (
            "Потяните мышью по области, которую нужно замазать. "
            "Зоны применяются ко всему ролику (статичная цензура)."
        ),
        "censor.editor_frame": "Кадр:",
        "censor.editor_block": "Размер пикселей:",
        "censor.editor_block_tip": "Чем больше — грубее мозаика (типично 12–24 для Pixiv).",
        "censor.editor_zones": "Зоны:",
        "censor.editor_remove": "Удалить зону",
        "censor.editor_clear": "Очистить все",
        "censor.editor_clear_confirm": "Удалить все зоны цензуры для этого ролика?",
        "censor.editor_need_zone": "Добавьте хотя бы одну зону (потяните мышью по кадру).",
        "censor.editor_frame_fail": "Не удалось загрузить кадр:\n{error}",
        "censor.zone_item": "#{n}: {w}×{h} @ ({x}, {y}), пиксель {block}",
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
        "common.browse": "参照…",
        "common.content_suite": "ContentSuite",
        "common.add": "追加…",
        "common.remove": "削除",
        "common.save": "保存",
        "common.cancel": "キャンセル",
        "common.ok": "OK",
        "menu.about": "ContentSuiteについて…",
        "about.title": "ContentSuiteについて",
        "about.body": (
            "<h2 style='margin-top:0'>{app}</h2>"
            "<p style='color:#666'>v{version}</p>"
            "<p>作成: <a href='{author_url}'>{author}</a><br>"
            "<a href='{repo_url}'>GitHubリポジトリ</a></p>"
            "<p><b>{ai_label}</b><br>"
            "共同開発: {ai_coauthor} · {ai_tool}</p>"
        ),
        "common.dpi": "DPI",
        "common.fps": "FPS",
        "common.not_selected": "（未選択）",
        "folder.placeholder": "フォルダを選択…",
        "folder.dialog": "フォルダ選択 — {label}",
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
        "censor.input": "入力（動画）:",
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
            "1) クリップ選択 · 2) 「モザイクエディタ」— 範囲をドラッグ · "
            "3) 「エクスポート」→ pixiv/name_1.mp4。ゾーンはクリップ全体に固定。"
        ),
        "censor.warn_pack_name": "パック名（プレフィックス）を入力してください。",
        "censor.warn_one_clip": "モザイクエディタ用に1本選択してください。",
        "censor.warn_no_video": "エクスポートする動画がありません。",
        "censor.warn_output": "出力フォルダを指定してください。",
        "censor.missing_zones": (
            "{count} 本にモザイクゾーンがありません ({names}{extra})。\n"
            "続行してスキップしますか？"
        ),
        "censor.and_more": " 他{n}本",
        "censor.done": "エクスポート: {done} / {total}\n{path}",
        "censor.editor_title": "モザイク — {name}",
        "censor.editor_hint": (
            "モザイクしたい範囲をドラッグ。ゾーンはクリップ全体に適用（固定モザイク）。"
        ),
        "censor.editor_frame": "フレーム:",
        "censor.editor_block": "ピクセルサイズ:",
        "censor.editor_block_tip": "大きいほど粗いモザイク（Pixivは通常12–24）。",
        "censor.editor_zones": "ゾーン:",
        "censor.editor_remove": "ゾーン削除",
        "censor.editor_clear": "すべてクリア",
        "censor.editor_clear_confirm": "このクリップのモザイクゾーンをすべて削除しますか？",
        "censor.editor_need_zone": "ゾーンを1つ以上追加（フレーム上でドラッグ）。",
        "censor.editor_frame_fail": "フレームを読み込めませんでした:\n{error}",
        "censor.zone_item": "#{n}: {w}×{h} @ ({x}, {y}), ピクセル {block}",
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
    },
}

SUPPORTED_LANGUAGES: tuple[tuple[str, str], ...] = (
    ("en", "lang.en"),
    ("ru", "lang.ru"),
    ("ja", "lang.ja"),
)