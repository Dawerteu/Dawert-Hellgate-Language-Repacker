# Dawert Language Repacker

Cross-platform repacker for Hellgate London / London2038 localized archives.

It keeps the game runtime language as `English`, then merges another language's cooked string tables into the English string tables. This avoids the usual London2038 `missing string` problem caused by setting `Data/language.dat` to `Czech`, `French`, etc.

## Requirements

- Python 3.8 or newer.
- A Hellgate London / London2038 folder containing `Data/`.
- Localized archives in `Data/`, for example:
  - `hellgate_localized000.dat/.idx`
  - `mp_hellgate_localized_*.dat/.idx`

No external Python packages are required.

## Setup Dependencies

The repacker only needs Python 3.8+ and the Python standard library.

On Linux/macOS:

```bash
cd "dawert-language repacker"
chmod +x setup-linux.sh
./setup-linux.sh
```

The setup detects the OS/package manager and installs Python through the system
package manager when needed. Supported Linux managers include `apt`, `dnf`,
`yum`, `pacman`, `zypper`, `apk`, `xbps-install`, `eopkg`, and `emerge`.
On macOS it uses Homebrew if available.

On Windows, double-click:

```text
setup-windows.bat
```

Or run PowerShell:

```powershell
.\setup-windows.ps1
```

The Windows setup checks for `py`/`python`, then tries `winget`, then `choco`,
and finally downloads the official Python installer from python.org if needed.
After installation it verifies `repacker.py --help`.

If setup fails, see:

```text
troubleshooting/
```

It contains separate Windows and Linux fallback files in English, Czech,
Russian, Polish, Hungarian, Italian, French, and Spanish.

## Start On Linux

```bash
cd "dawert-language repacker"
chmod +x start-linux.sh
./start-linux.sh
```

The launcher opens a numbered menu with the DAWERT banner. You can choose:

```text
== Install ==
1. Install language
2. Custom install with toggle list for tables you do not want translated
3. ASCII/font-safe fallback

== Manual CSV Translation ==
4. Export only London2038 strings not translated automatically
5. Export all London2038 strings
6. Export every English string
7. Import translated CSV

== Maintenance ==
8. List languages
9. Restore originals
10. Dry run normal install
11. Refresh clean backup after official launcher update
12. Official checksum updater
```

At startup the launcher asks for script UI language. Available UI languages:

- English
- Czech
- Russian
- Polish
- Hungarian
- Italian
- French
- Spanish

Or direct CLI:

```bash
python3 repacker.py --game-dir "/path/to/Hellgate London" --language czech
```

Auto-find mode tries common London2038/Hellgate locations:

```bash
python3 repacker.py --auto-find --language czech
```

By default this patches the English runtime font atlas to the selected
language's atlas. This is the real font fix for missing Czech, Polish,
Hungarian, Russian, and similar glyphs while still keeping:

```text
Data/language.dat = Language=English
```

## Start On Windows

Double-click:

```text
start-windows.bat
```

The Windows launcher opens the same numbered menu as Linux.

Or run PowerShell:

```powershell
.\start-windows.ps1
```

Or direct CLI:

```powershell
py -3 repacker.py --game-dir "C:\Program Files\Flagship Studios\Hellgate London" --language czech
```

Auto-find mode also works on Windows:

```powershell
py -3 repacker.py --auto-find --language czech
```

## Play Without Launcher Overwrite

London2038 `Launcher.exe` can check localized archive sizes and download the
official files again. If you start the launcher after installing a translation,
it may overwrite the repacked `.dat/.idx` files every time.

Use the direct play launcher for normal play:

Windows:

```text
play-windows.bat
```

Linux:

```bash
chmod +x play-linux.sh
./play-linux.sh
```

The direct play launcher has two modes:

```text
1. Play now
2. Official checksum update
```

Mode 1 applies the selected language repack, then starts:

```text
MP_x64\London2038_dx9_x64.exe
```

Mode 2 is for official updates or repair. It reads `Patcher.xml`, downloads the
latest `checksums.xml` from the official `RemoteDirectory`, verifies MD5/size,
downloads changed official files from that same server, refreshes the clean
backup, then applies the selected language again. This avoids the launcher
refusing modified data while still keeping translated files for play.

You can also run the updater directly:

Windows:

```text
update-windows.bat
```

Linux:

```bash
chmod +x update-linux.sh
./update-linux.sh
```

Direct CLI:

```bash
python3 repacker.py --auto-find --action checksum-update --language czech
```

The play and update launchers remember the last selected language in:

```text
dawert-launcher.conf
```

Next time, pressing Enter uses that saved language.

## What It Asks For

- `Hellgate game folder`: the folder that contains `Launcher.exe` and `Data`.
  The interactive launcher first tries to find this folder automatically. If it finds candidates, press Enter to use the first one.
- `Action`:
  - `install`: build and install the repacked archives. Default includes loading tips.
  - `export-csv`: export every English string row to CSV.
  - `import-csv`: import filled CSV translations by `StringID`.
  - `list`: show available source languages found in the archives.
  - `restore`: restore original localized archives from backup.
  - `refresh-backup`: refresh the clean backup after an official launcher update.
  - `checksum-update`: verify/download official files from the London2038 checksum manifest, refresh backup, then optionally reinstall language.
- `Source language`: language folder to merge into English, for example:
  - `czech`
  - `french`
  - `spanish`
  - `italian`
  - `polish`
  - `russian`
  - `hungarian`
- `Exclude tables`: default is nothing. In menu option 2, selected tables are kept in English.
- `Patch font atlas`: default is yes. This is the real font fix. It replaces
  English `fonts_atlas.xml` with the selected language's existing atlas.
- `Font-safe mode`: fallback only. It strips accents if a setup still renders
  translated glyphs incorrectly.

## Default Install

By default, menu option 1 installs the selected language with loading tips and
the real font atlas fix:

```text
1. Install language
```

The menu keeps the wording simple, but install still patches the matching font
atlas automatically. This is required so Czech/Polish/Russian/etc. glyphs render
properly while the game stays on `Language=English`.

Direct CLI equivalent:

```bash
python3 repacker.py --game-dir "/path/to/Hellgate London" --language czech --exclude none
```

For custom installs, choose menu option 2. It shows a toggle list where `[X]`
means "keep this table in English / do not translate it".

## CSV Export And Import

The CSV workflow is for missing London2038-only strings or custom translations.
It keeps the game running as `Language=English`.

Export only London2038 strings that automatic language merge cannot translate:

```bash
python3 repacker.py --auto-find --action export-csv --csv-scope london2038-untranslated --language czech
```

Default output:

```text
Data/dawertrepacker/exports/london2038-untranslated-english-strings.csv
```

This compares London2038 English rows against the selected source language by
`StringID`. Rows that already have a Czech/Polish/Russian/etc. source
translation are skipped.

Export all London2038 strings:

```bash
python3 repacker.py --auto-find --action export-csv --csv-scope london2038
```

Default output:

```text
Data/dawertrepacker/exports/london2038-english-strings.csv
```

Export every English string:

```bash
python3 repacker.py --auto-find --action export-csv
```

Default output:

```text
Data/dawertrepacker/exports/hellgate-english-strings.csv
```

CSV columns:

```text
Archive, Table, StringID, English, Translation, Directory, Attributes
```

Fill only the `Translation` column. Empty translations stay English.
Keep placeholder tokens exactly as they are, for example:

```text
Rare [object] -> Vzacne [object]
Damage: %d -> Poskozeni: %d
<color=red>Warning</color> -> <color=red>Varovani</color>
```

Do not translate or edit `Archive`, `Table`, or `StringID`.

Import the filled CSV:

```bash
python3 repacker.py --auto-find --action import-csv --language czech --csv "Data/dawertrepacker/exports/london2038-untranslated-english-strings.csv"
```

When `--language czech` is used, import is layered:

```text
clean English originals -> automatic Czech merge -> filled CSV translations
```

That means a CSV with only the missing London2038 rows acts as an add-on. Rows
not present in the CSV still use the automatic Czech/Polish/Russian/etc. merge,
and empty `Translation` cells stay English.

Menu option 4 does the same interactively.

## Backup And Restore

All generated files are stored under:

```text
Data/dawertrepacker/
```

On first install/export/import, the tool creates:

```text
Data/dawertrepacker/backup/original/
```

It uses that as the clean source for future repacks. Before every install it also stores a timestamped snapshot:

```text
Data/dawertrepacker/backup/before-install-YYYYMMDD-HHMMSS/
```

Repacked archives and logs go to:

```text
Data/dawertrepacker/output/
```

Every run also gets a full console log:

```text
Data/dawertrepacker/logs/YYYYMMDD-HHMMSS-microseconds-action.log
```

The log includes detailed IDX decrypt/archive parsing information:

```text
[detail] IDX decrypt start
[detail] try crypt=old/l2038
[detail] success crypt=...
[detail] string table parsed
[detail] entries parsed
```

To reduce decrypt logging:

```bash
python3 repacker.py --auto-find --action list --quiet-decrypt-log
```

The original backup also includes:

```text
Data/dawertrepacker/backup/original/language.dat
```

On install, CSV import, and restore, the tool auto-fixes:

```text
Data/language.dat = Language=English
```

This is intentional for London2038 stability and avoids the `missing string`
state caused by running the client as `Language=Czech`, `Language=Polish`, etc.

To restore the original localized archives:

```bash
python3 repacker.py --game-dir "/path/to/Hellgate London" --action restore
```

The restore also writes:

```text
Data/language.dat = Language=English
```

## How It Works

1. Reads and decrypts Hellgate `.idx` files.
2. Finds `data\excel\strings\<language>\strings_*.xls.uni.cooked`.
3. Finds matching English string tables.
4. Parses cooked string rows by `StringID`.
5. Replaces only text values in English rows, keeping English row structure and attributes.
6. Leaves English rows without a matching translation untouched.
7. Compresses the rebuilt cooked table with zlib.
8. Appends it to the `.dat` file.
9. Updates offsets and sizes in the `.idx`.
10. Re-encrypts the `.idx`.

This is a merge, not a full language switch.

## Font Fix And Font-Safe Fallback

Some Hellgate fonts do not contain every translated glyph. Czech accents or other Latin extended characters can render with the wrong font, as boxes, or with broken spacing.

The normal fix is enabled by default. The repacker replaces:

```text
data\uix\xml\fonts_atlas.xml
```

with the selected language atlas, for example:

```text
data\uix\xml\czech_fonts_atlas.xml
data\uix\xml\polish_fonts_atlas.xml
data\uix\xml\russian_fonts_atlas.xml
```

This uses the original game font assets for that language, without switching
`language.dat` away from English.

To disable the atlas patch:

```bash
python3 repacker.py --auto-find --language czech --no-font-patch
```

If the atlas patch still does not render acceptably on a specific setup, use
ASCII/font-safe mode as a fallback:

```bash
python3 repacker.py --auto-find --language czech --font-safe
```

This keeps the translation but strips accents and replaces common unsupported symbols:

```text
Žádné mise -> Zadne mise
Mise dokončena -> Mise dokoncena
“text” -> "text"
… -> ...
```

This is less pretty, but it avoids most custom-font rendering problems. If the built-in language atlas is still not enough, the next step would be editing the game's font assets and glyph maps, which is much more invasive and language-specific.

## Notes

- The game should still run with `Data/language.dat` set to `Language=English`.
- New London2038-only strings that do not exist in the selected source language remain English.
- If the game freezes or crashes, run `restore`.
- The folder path can contain spaces.
