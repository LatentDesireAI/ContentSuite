# Release checklist

## Automated build (GitHub Actions)

On every tag `v*` (e.g. `v1.0.1`), workflow **Release build** (`.github/workflows/release.yml`):

1. Runs on `windows-latest`
2. PyInstaller → `ContentSuite-win64.zip`
3. Creates/updates the GitHub Release and uploads the zip

```bat
git tag v1.0.1
git push origin v1.0.1
```

Manual run: **Actions → Release build → Run workflow**.

Match `core/credits.py` → `APP_VERSION` when bumping versions.

## Changelog (highlights)

### v1.1.3
- **Art Checker** tab — prompt JSON vs output folder, OK/MISS grid, folder watch, duplicate-file variants (wheel on hover)
- Unified **tile selection** styling on Images, Video, Pixiv Censor, and Art Checker grids
- **Images** grid sort by name or date (newest)

### v1.1.2
- MP4 mobile playback fixes (`yuv420p`, `faststart`, safe remux/re-encode)
- Reliable batch encode via temp file + validation before move

## Build (Windows, local)

Requirements on the build machine: Python 3.11+, same as development.

```bat
build_release.bat
```

Output:

- `dist\ContentSuite\` — folder with `ContentSuite.exe`
- `dist\ContentSuite-win64.zip` — upload this to GitHub Releases

**ffmpeg is not bundled.** Users still need [ffmpeg](https://ffmpeg.org/) and `ffprobe` in `PATH` (same as the source install).

## Publish on GitHub (manual fallback)

If CI is unavailable, build locally (`build_release.bat`) and upload `dist/ContentSuite-win64.zip` to the release page.

With GitHub CLI:

```bat
gh release create v1.0.1 dist\ContentSuite-win64.zip ^
  --title "ContentSuite v1.0.1 (Windows)" ^
  --notes "Windows portable build. Requires ffmpeg in PATH. See README."
```

Linux binary: add an `ubuntu-latest` job to the workflow later (same PyInstaller spec).