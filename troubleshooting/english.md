# Troubleshooting - English

## Windows

- If setup fails, install Python 3.8+ manually from `https://www.python.org/downloads/windows/`.
- During install, enable `Add python.exe to PATH`.
- Open `cmd` in the `dawert-language repacker` folder and test:

```bat
py -3 --version
python --version
```

- Start with:

```bat
start-windows.bat
```

- If PowerShell blocks scripts, use `start-windows.bat` instead of `.ps1`.
- If `py` is missing but `python` works, the BAT launcher will use `python`.
- If `Launcher.exe` refuses changed data or downloads original localized files again, do not use it for normal play. Start the game with `play-windows.bat` instead.

## Linux

- If setup fails, install Python manually with your package manager:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Then run:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

- If `Launcher.exe` overwrites translated files, start the game with:

```bash
chmod +x play-linux.sh
./play-linux.sh
```

The `play-*` script has a normal play mode and an official update mode. Update mode restores clean data first, starts `Launcher.exe`, refreshes the clean backup after it exits, then can apply the translation again.

## Logs And Restore

- Logs are in `Data/dawertrepacker/logs/`.
- Backups are in `Data/dawertrepacker/backup/`.
- Restore from the menu or run:

```bash
python3 repacker.py --auto-find --action restore
```

The tool keeps `Data/language.dat` as `Language=English`.
