# WordSense 1.0.5

**English** · [简体中文](README.zh-CN.md)

A local-first Windows English writing editor that colors words by your recorded understanding level. Built with Python 3.11+, PySide6 and SQLite. Editing and vocabulary lookup require no account, network API or server.

![WordSense with the Ink Slate theme](docs/preview.png)

## Features

- Instant ASCII word recognition with case-insensitive lookup and original spelling preserved.
- Green `#A7C080`: fully understood. Blue `#7FBBB3`: somewhat unclear. Red `#E67E80`: not understood. Yellow `#DBBC7F`: unrecorded or currently being typed.
- Search recorded words or Chinese meanings in the dictionary sidebar; vocabulary updates recolor existing text.
- Native selection, copy, paste, undo and redo. Enter inserts a new paragraph with two spaces; visual wrapping inserts no characters. Large and multiline pastes are processed in batches.
- Daily UTF-8 Markdown documents, date switching, export, configurable article folders and verified migration/cleanup.
- One shared SQLite vocabulary across every article, with an independently configurable database location.
- Ink Slate colors, a book-shaped W logo and a clearly labeled document menu. The current application UI uses Chinese labels; documentation is bilingual.

## Download the Windows build

Get `WordSense-v1.0.5-Windows-x64.zip` from the [v1.0.5 release](https://github.com/snowfeeling3/WordSense/releases/tag/v1.0.5). Extract the complete folder and double-click `WordSense.exe`. Python is included; keep `_internal` beside the executable.

Do not run the intermediate EXE under `build/` or copy the EXE alone. This is an unsigned portable Windows x64 package with a SHA-256 checksum, usage instructions and third-party license texts. It contains no user documents or vocabulary.

## Run from source

In PowerShell with Python 3.11+ installed:

```powershell
git clone https://github.com/snowfeeling3/WordSense.git
cd WordSense
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m wordsense
```

After installing dependencies, `start_wordsense.cmd` also launches the source application. `WordSense.cmd` launches an already downloaded or built `dist/WordSense-v1.0.5/WordSense.exe`; that file is not included in a fresh source clone.

Validated on Windows 11, Python 3.13.5 and PySide6 6.8.3. The code uses Qt, but full desktop behavior on other platforms has not been verified.

## Keyboard and menus

| Action | Shortcut or UI entry |
| --- | --- |
| Focus the word field | Ctrl+L; selects existing content for replacement |
| Move from the word to its meaning | Enter in the word field |
| Save vocabulary and return to writing | Enter in the meaning field, or 保存 / 更新 (Save / Update) |
| Save the current article | Ctrl+S |
| Export Markdown | Ctrl+Shift+S |
| Change date or storage folders | Document menu at the top right |

A token being edited stays yellow until a delimiter completes it. Unknown words remain yellow. Changing a vocabulary level triggers a separate full highlight refresh. Markdown contains plain text, not colors; reopening an old article applies the current shared vocabulary. Startup opens today's document. Writing across midnight does not silently switch its date.

The menu includes 设置文档位置 (Set document location), 设置词库位置 (Set vocabulary location), and separate cleanup actions for old files. The article folder and vocabulary location can be changed independently.

## Data, migration and backup

The fixed Windows user directory is `%LOCALAPPDATA%\WordSense`, independent of the program's location and working directory.

- **Vocabulary:** `wordsense.sqlite3` by default; shared by all dates and current source/frozen builds.
- **Articles:** `documents/YYYY-MM-DD.md` by default; configurable from the document menu.
- **Configuration:** `settings.json` records the actual database path. The current database's `app_meta` table records the article directory.
- **Database relocation:** uses SQLite backup and integrity/data checks before switching the path and cleaning the old database. Existing destination databases are never overwritten. A missing configured database raises an error instead of creating an empty replacement.
- **Article relocation:** verifies SHA-256 before removing originals. Cleanup affects managed dated Markdown and WordSense temporary files; other files are preserved. Busy old files can be cleaned later.

Vocabulary saves commit explicit SQLite transactions. Article changes are saved atomically by one background worker about 700 ms after editing pauses. That single-shot timer only coalesces disk writes; highlighting has no debounce or polling delay. Date switches and normal shutdown wait for the latest save. Forced termination may lose the newest unsaved input.

For backup, close the app and copy the fixed configuration directory, actual database directory and actual article directory. After relocating the database, use this version or newer; earlier versions do not understand the custom database pointer.

Legacy level 1 becomes level 2: the old two intermediate categories are merged into somewhat unclear. Words, meanings, IDs and timestamps are preserved. Current stored values are 3 = understood, 2 = unclear, 0 = not understood.

## Tests and performance

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m benchmarks.benchmark
```

The current 48 tests cover coloring, editing boundaries, bulk paste, UTF-16, undo/redo, keyboard flow, daily storage, directory migrations, collision protection and legacy vocabulary conversion. Persistence tests use temporary databases and files.

Historical local measurements: 120,000-character multiline paste 74.632 ms; two-key local edits median 0.076 ms and P95 0.093 ms, affecting at most two blocks. These offscreen measurements exclude screen presentation and disk writes; results vary by machine. See [bilingual architecture and validation](docs/ARCHITECTURE.md), [raw benchmark data](benchmarks/results.json).

Highlighting is paragraph-granular, so very long single paragraphs, initial loads and global vocabulary refreshes may occupy the GUI thread briefly. Undo history and cursor position are not preserved across documents or restarts. Avoid concurrent writers or old app instances editing the same files.

## Build a Windows distribution

On Windows with PowerShell 7:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\packaging\build.ps1
.\.venv\Scripts\python.exe -m tools.verify_release
```

The build generates a portable folder, ZIP and checksum, then validates the packaged executable. Build output is excluded from Git. License preparation needs internet access on its first run; normal app editing does not.

## Project layout and third-party components

`wordsense/` contains the app; `tests/` the tests; `tools/` verification and icon tooling; `packaging/` PyInstaller configuration and notices; `assets/` the logo; `benchmarks/` performance scripts; and `docs/` documentation and validation records.

Colors are based on [Everforest](https://github.com/sainnhe/everforest). Third-party components are documented in [THIRD_PARTY_NOTICES.txt](packaging/THIRD_PARTY_NOTICES.txt) and [license texts](packaging/licenses). WordSense application code is available under the [MIT license](LICENSE). Third-party components retain their own licenses.
