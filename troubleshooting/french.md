# Troubleshooting - Français

## Windows

- Si le setup échoue, installe Python 3.8+ manuellement depuis `https://www.python.org/downloads/windows/`.
- Pendant l'installation, coche `Add python.exe to PATH`.
- Ouvre `cmd` dans le dossier `dawert-language repacker` et teste:

```bat
py -3 --version
python --version
```

- Lance:

```bat
start-windows.bat
```

- Si PowerShell bloque les scripts, utilise `.bat` au lieu de `.ps1`.
- Si `py` manque mais `python` fonctionne, le launcher BAT utilisera `python`.

## Linux

- Si le setup échoue, installe Python manuellement:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Puis lance:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

## Logs et restauration

- Logs: `Data/dawertrepacker/logs/`.
- Backups: `Data/dawertrepacker/backup/`.
- Restore depuis le menu ou avec:

```bash
python3 repacker.py --auto-find --action restore
```

L'outil garde `Data/language.dat` en `Language=English`.
