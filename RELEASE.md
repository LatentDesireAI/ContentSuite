# Release checklist

## Build (Windows)

Requirements on the build machine: Python 3.11+, same as development.

```bat
build_release.bat
```

Output:

- `dist\ContentSuite\` — folder with `ContentSuite.exe`
- `dist\ContentSuite-win64.zip` — upload this to GitHub Releases

**ffmpeg is not bundled.** Users still need [ffmpeg](https://ffmpeg.org/) and `ffprobe` in `PATH` (same as the source install).

## Publish on GitHub

1. Tag: `v1.0.0` (match `core/credits.py` → `APP_VERSION`)
2. Title: `ContentSuite v1.0.0 (Windows)`
3. Attach: `dist/ContentSuite-win64.zip`
4. Notes (short):

   - Windows 10/11 portable build — unzip and run `ContentSuite.exe`
   - Requires ffmpeg/ffprobe in PATH
   - Config: `%APPDATA%\ContentSuite\`
   - MIT license

With GitHub CLI:

```bat
gh release create v1.0.0 dist\ContentSuite-win64.zip ^
  --title "ContentSuite v1.0.0 (Windows)" ^
  --notes "Windows portable build. Requires ffmpeg in PATH. See README."
```

Linux binary: build on a Linux machine with the same spec (PyInstaller); not produced from Windows CI in this repo yet.